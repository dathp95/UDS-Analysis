"""Pure clipboard exchange; imported Results never become diagnostic runtime state."""
import csv
from dataclasses import dataclass
import io

from core.diagnostic_sequence import DiagnosticStep
from repositories.diagnostic_sequence_repository import DiagnosticSequenceRepository as Native

HEADERS = ('Step', 'Test sequence name', 'ECU', 'Payload(HEX)', 'Delay(ms)', 'Repeat',
           'Expected Response (HEX)', 'Results', 'Comment')
MAX_TEXT = 2 * 1024 * 1024
MAX_ROWS = 2000


@dataclass(frozen=True)
class SequenceImport:
    steps: tuple[DiagnosticStep, ...]
    diagnostics: tuple[str, ...]


def export_sequence_text(steps, results=()):
    output = io.StringIO(newline='')
    writer = csv.writer(output, delimiter='\t', lineterminator='\n')
    writer.writerow(HEADERS)
    results = tuple(results)
    for index, step in enumerate(steps):
        writer.writerow((step.step, step.sequence_name, step.ecu, step.request,
                         '' if step.delay_ms is None else step.delay_ms, step.repeat,
                         step.expected_response, results[index] if index < len(results) else '', step.comment))
    return output.getvalue()


def parse_sequence_text(text, *, ecu_names=None):
    if not isinstance(text, str) or len(text) > MAX_TEXT:
        raise ValueError('Input exceeds the 2,097,152-character clipboard limit.')
    reader = None
    for delimiter in ('\t', ','):
        candidate = csv.reader(io.StringIO(text.lstrip('\ufeff'), newline=''), delimiter=delimiter, strict=True)
        try:
            if tuple(next(candidate, ())) == HEADERS:
                reader = candidate
                break
        except csv.Error:
            continue
    if reader is None:
        raise ValueError('Row 1: expected exactly these columns: ' + ' | '.join(HEADERS))
    steps, diagnostics, seen = [], [], set()
    while True:
        source_row = reader.line_num + 1
        try:
            row = next(reader)
        except StopIteration:
            break
        except csv.Error:
            raise ValueError(f'Row {source_row}: invalid quoted TSV/CSV.') from None
        if not row:
            continue
        if len(row) != 9:
            raise ValueError(f'Row {source_row}: expected 9 cells, got {len(row)}.')
        try:
            number = int(row[0])
            name, ecu = row[1].strip(), row[2].strip()
            delay = int(row[4]) if row[4].strip() else None
            repeat = int(row[5])
            if number < 1 or number in seen or not name or (delay is not None and delay < 0) or repeat < 1:
                raise ValueError('Step must be positive/unique, sequence name nonempty, delay >= 0 and repeat >= 1.')
            request = Native._normalize_hex(row[3], 'Payload(HEX)')
            expected = Native._normalize_hex(row[6], 'Expected Response (HEX)', allow_empty=True)
        except (ValueError, TypeError) as error:
            raise ValueError(f'Row {source_row}: {error}') from None
        seen.add(number)
        steps.append(DiagnosticStep(number, name, ecu, request, delay, repeat, expected, comment=row[8]))
        if len(steps) > MAX_ROWS:
            raise ValueError(f'Row {source_row}: at most {MAX_ROWS} rows may be imported.')
        if ecu_names is not None and (not ecu or ecu not in ecu_names):
            diagnostics.append(f'Row {source_row}: unresolved ECU {ecu!r}; selector will be empty.')
        if row[7].strip() not in ('', '—'):
            diagnostics.append(f'Row {source_row}: imported Results ignored; actual transport execution is required.')
    if not steps:
        raise ValueError('Row 2: no diagnostic rows to import.')
    return SequenceImport(tuple(steps), tuple(diagnostics))
