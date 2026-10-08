import json
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric import rsa

from license.activation import (
    ACTIVATION_TOKEN_VERSION,
    MAX_ACTIVATION_TOKEN_LENGTH,
    ActivationStorage,
    ActivationTokenError,
    create_activation_token,
    validate_activation_token,
)
from license.device_identity import DeviceIdentity
from license.exceptions import LicenseError
from license.manager import LicenseManager


def _key_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=3072,
    )
    return private_key, private_key.public_key()


def _payload(device_id, *, expires_at=None, version=ACTIVATION_TOKEN_VERSION):
    issued_at = datetime(2026, 1, 1, tzinfo=UTC)
    expires_at = expires_at or issued_at + timedelta(days=30)
    return {
        "version": version,
        "license_id": "lic-test-001",
        "device_id": device_id,
        "customer": "Test Customer",
        "edition": "Professional",
        "issued_at": issued_at.isoformat().replace("+00:00", "Z"),
        "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
    }


class DeviceIdentityTests(unittest.TestCase):

    def test_device_id_is_stable_hashed_and_does_not_expose_machine_guid(self):
        identity = DeviceIdentity(
            identifier_provider=lambda: " {00112233-4455-6677-8899-AABBCCDDEEFF} "
        )

        first = identity.get_device_id()
        second = identity.get_device_id()

        self.assertEqual(first, second)
        self.assertRegex(first, r"^VC-[0-9A-F]{4}(-[0-9A-F]{4}){4}$")
        self.assertNotIn("00112233", first)
        self.assertNotIn("AABBCCDDEEFF", first)

    def test_device_id_fails_closed_without_any_identifier(self):
        identity = DeviceIdentity(identifier_provider=lambda: "")

        with self.assertRaises(LicenseError):
            identity.get_device_id()


class ActivationTokenTests(unittest.TestCase):

    def test_valid_signed_activation_returns_license(self):
        private_key, public_key = _key_pair()
        device_id = "VC-1111-2222-3333-4444-5555"
        token = create_activation_token(_payload(device_id), private_key)

        license_model = validate_activation_token(
            token,
            expected_device_id=device_id,
            public_key=public_key,
            now=datetime(2026, 1, 2, tzinfo=UTC),
        )

        self.assertEqual(license_model.customer, "Test Customer")
        self.assertEqual(license_model.edition, "Professional")
        self.assertEqual(license_model.metadata["license_id"], "lic-test-001")

    def test_modified_payload_rejects_signature(self):
        private_key, public_key = _key_pair()
        device_id = "VC-1111-2222-3333-4444-5555"
        token = create_activation_token(_payload(device_id), private_key)
        encoded_payload, encoded_signature = token.split(".", 1)
        tampered_payload = _payload(device_id)
        tampered_payload["customer"] = "Attacker"
        tampered_token = (
            create_activation_token(tampered_payload, private_key).split(".", 1)[0]
            + "."
            + encoded_signature
        )
        self.assertNotEqual(encoded_payload, tampered_token.split(".", 1)[0])

        with self.assertRaises(ActivationTokenError):
            validate_activation_token(
                tampered_token,
                expected_device_id=device_id,
                public_key=public_key,
                now=datetime(2026, 1, 2, tzinfo=UTC),
            )

    def test_wrong_device_expired_malformed_and_unsupported_tokens_reject(self):
        private_key, public_key = _key_pair()
        device_id = "VC-1111-2222-3333-4444-5555"

        wrong_device_token = create_activation_token(_payload(device_id), private_key)
        with self.assertRaises(ActivationTokenError):
            validate_activation_token(
                wrong_device_token,
                expected_device_id="VC-AAAA-BBBB-CCCC-DDDD-EEEE",
                public_key=public_key,
                now=datetime(2026, 1, 2, tzinfo=UTC),
            )

        expired_token = create_activation_token(
            _payload(device_id, expires_at=datetime(2026, 1, 1, tzinfo=UTC)),
            private_key,
        )
        with self.assertRaises(ActivationTokenError):
            validate_activation_token(
                expired_token,
                expected_device_id=device_id,
                public_key=public_key,
                now=datetime(2026, 1, 2, tzinfo=UTC),
            )

        with self.assertRaises(ActivationTokenError):
            validate_activation_token(
                "not-a-valid-token",
                expected_device_id=device_id,
                public_key=public_key,
                now=datetime(2026, 1, 2, tzinfo=UTC),
            )

        unsupported_token = create_activation_token(
            _payload(device_id, version=999),
            private_key,
        )
        with self.assertRaises(ActivationTokenError):
            validate_activation_token(
                unsupported_token,
                expected_device_id=device_id,
                public_key=public_key,
                now=datetime(2026, 1, 2, tzinfo=UTC),
            )

    def test_future_issued_at_and_non_canonical_base64_reject(self):
        private_key, public_key = _key_pair()
        device_id = "VC-1111-2222-3333-4444-5555"
        future_payload = _payload(device_id)
        future_payload["issued_at"] = "2026-01-03T00:00:00Z"
        future_payload["expires_at"] = "2026-02-01T00:00:00Z"
        future_token = create_activation_token(future_payload, private_key)

        with self.assertRaises(ActivationTokenError):
            validate_activation_token(
                future_token,
                expected_device_id=device_id,
                public_key=public_key,
                now=datetime(2026, 1, 2, tzinfo=UTC),
            )

        token = create_activation_token(_payload(device_id), private_key)
        encoded_payload, encoded_signature = token.split(".", 1)
        padded_token = f"{encoded_payload}=.{encoded_signature}"

        with self.assertRaises(ActivationTokenError):
            validate_activation_token(
                padded_token,
                expected_device_id=device_id,
                public_key=public_key,
                now=datetime(2026, 1, 2, tzinfo=UTC),
            )

    def test_attacker_controlled_public_pem_is_not_trusted(self):
        trusted_private_key, trusted_public_key = _key_pair()
        attacker_private_key, _attacker_public_key = _key_pair()
        device_id = "VC-1111-2222-3333-4444-5555"
        attacker_token = create_activation_token(
            _payload(device_id),
            attacker_private_key,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            attacker_public_pem = Path(temp_dir) / "public.pem"
            attacker_public_pem.write_text("attacker controlled", encoding="utf-8")

            with self.assertRaises(ActivationTokenError):
                validate_activation_token(
                    attacker_token,
                    expected_device_id=device_id,
                    public_key=trusted_public_key,
                    now=datetime(2026, 1, 2, tzinfo=UTC),
                )

        trusted_token = create_activation_token(_payload(device_id), trusted_private_key)
        self.assertEqual(
            validate_activation_token(
                trusted_token,
                expected_device_id=device_id,
                public_key=trusted_public_key,
                now=datetime(2026, 1, 2, tzinfo=UTC),
            ).customer,
            "Test Customer",
        )


class ActivationStorageAndManagerTests(unittest.TestCase):

    def test_activation_persists_and_renews_with_new_key(self):
        private_key, public_key = _key_pair()
        device_id = "VC-1111-2222-3333-4444-5555"
        first_token = create_activation_token(_payload(device_id), private_key)
        renewed_token = create_activation_token(
            _payload(
                device_id,
                expires_at=datetime(2026, 3, 1, tzinfo=UTC),
            ),
            private_key,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "activation.dat"

            with patch(
                "license.manager.ACTIVATION_FILE_PATH",
                storage_path,
            ), patch.object(
                LicenseManager,
                "get_device_id",
                return_value=device_id,
            ), patch(
                "license.activation.load_trusted_public_key",
                return_value=public_key,
            ), patch(
                "license.activation.datetime"
            ) as datetime_mock:
                datetime_mock.now.return_value = datetime(2026, 1, 2, tzinfo=UTC)
                datetime_mock.fromisoformat.side_effect = datetime.fromisoformat

                result = LicenseManager.activate(first_token)
                self.assertTrue(result.success)
                self.assertTrue(storage_path.is_file())
                self.assertTrue(LicenseManager.get_status().is_valid)

                renewed = LicenseManager.activate(renewed_token)
            self.assertTrue(renewed.success)
            self.assertEqual(renewed.license.expire_date.date().isoformat(), "2026-03-01")

    def test_corrupt_storage_and_legacy_license_do_not_activate(self):
        private_key, public_key = _key_pair()
        device_id = "VC-1111-2222-3333-4444-5555"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            storage_path = temp_path / "activation.dat"
            storage_path.write_text("corrupt-token", encoding="utf-8")
            (temp_path / "license.lic").write_text(
                json.dumps({"legacy": "should not bypass"}),
                encoding="utf-8",
            )

            with patch(
                "license.manager.ACTIVATION_FILE_PATH",
                storage_path,
            ), patch.object(
                LicenseManager,
                "get_device_id",
                return_value=device_id,
            ), patch(
                "license.activation.load_trusted_public_key",
                return_value=public_key,
            ):
                status = LicenseManager.get_status()

            self.assertFalse(status.is_valid)
            self.assertIn("activation", status.error_message.lower())

    def test_activate_returns_failure_when_device_identity_is_unavailable(self):
        with patch.object(
            LicenseManager,
            "get_device_id",
            side_effect=LicenseError("no device id"),
        ):
            result = LicenseManager.activate("any-token")

        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "no device id")

    def test_storage_read_missing_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = ActivationStorage(Path(temp_dir) / "activation.dat")

            with self.assertRaises(LicenseError):
                storage.read()

    def test_storage_read_rejects_oversized_activation_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "activation.dat"
            storage_path.write_text(
                "A" * (MAX_ACTIVATION_TOKEN_LENGTH + 1),
                encoding="utf-8",
            )

            with self.assertRaises(ActivationTokenError):
                ActivationStorage(storage_path).read()


if __name__ == "__main__":
    unittest.main()
