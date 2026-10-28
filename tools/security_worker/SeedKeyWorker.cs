// MOCK ONLY. There is deliberately no native DLL loader or GenerateKeyEx delegate.
using System;
using System.Collections.Generic;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using System.Web.Script.Serialization;

internal static class SeedKeyWorker
{
    private const int MaxFrame = 4096;
    private static readonly JavaScriptSerializer Json = new JavaScriptSerializer { MaxJsonLength = MaxFrame, RecursionLimit = 4 };

    private static byte[] ReadExact(Stream stream, int count)
    {
        byte[] data = new byte[count];
        int used = 0;
        while (used < count)
        {
            int size = stream.Read(data, used, count - used);
            if (size == 0) throw new InvalidDataException();
            used += size;
        }
        return data;
    }

    private static void SkipSpace(string text, ref int index)
    {
        while (index < text.Length && Char.IsWhiteSpace(text[index])) index++;
    }

    private static string ReadString(string text, ref int index)
    {
        int start = index;
        if (index >= text.Length || text[index++] != '"') throw new InvalidDataException();
        while (index < text.Length)
        {
            char value = text[index++];
            if (value == '\\') { index++; continue; }
            if (value == '"') return Json.Deserialize<string>(text.Substring(start, index - start));
        }
        throw new InvalidDataException();
    }

    // Reject duplicate/unknown members and nested data before deserialization.
    private static void CheckMembers(string text)
    {
        HashSet<string> expected = new HashSet<string>(new string[] {
            "version", "request_id", "vehicle", "ecu", "level", "seed_hex", "output_size", "timeout_ms" });
        int index = 0;
        SkipSpace(text, ref index);
        if (index >= text.Length || text[index++] != '{') throw new InvalidDataException();
        while (true)
        {
            SkipSpace(text, ref index);
            string key = ReadString(text, ref index);
            if (!expected.Remove(key)) throw new InvalidDataException();
            SkipSpace(text, ref index);
            if (index >= text.Length || text[index++] != ':') throw new InvalidDataException();
            SkipSpace(text, ref index);
            if (index < text.Length && text[index] == '"') ReadString(text, ref index);
            else
            {
                int start = index;
                while (index < text.Length && text[index] != ',' && text[index] != '}') index++;
                if (!Regex.IsMatch(text.Substring(start, index - start).Trim(), "^-?[0-9]+$")) throw new InvalidDataException();
            }
            SkipSpace(text, ref index);
            if (index >= text.Length) throw new InvalidDataException();
            if (text[index++] == '}') break;
            if (text[index - 1] != ',') throw new InvalidDataException();
        }
        SkipSpace(text, ref index);
        if (index != text.Length || expected.Count != 0) throw new InvalidDataException();
    }

    private static int Number(Dictionary<string, object> request, string name, int minimum, int maximum)
    {
        object raw = request[name];
        if (!(raw is int) || (int)raw < minimum || (int)raw > maximum) throw new InvalidDataException();
        return (int)raw;
    }

    private static string Text(Dictionary<string, object> request, string name, int maximum)
    {
        string value = request[name] as string;
        if (String.IsNullOrEmpty(value) || value.Length > maximum) throw new InvalidDataException();
        foreach (char item in value) if (Char.IsControl(item)) throw new InvalidDataException();
        return value;
    }

    private static int Main(string[] args)
    {
        try
        {
            // /platform:x86 plus runtime verification; never AnyCPU.
            if (IntPtr.Size != 4 || args.Length != 1) return 2;
            if (args[0] == "--probe")
            {
                Console.Write("{\"version\":1,\"worker_bits\":32,\"mock_only\":true,\"native_enabled\":false}");
                return 0;
            }
            if (args[0] != "--mock") return 2;
            Stream input = Console.OpenStandardInput();
            int length = BitConverter.ToInt32(ReadExact(input, 4), 0);
            if (length < 1 || length > MaxFrame) return 2;
            byte[] frame = ReadExact(input, length);
            if (input.ReadByte() != -1) return 2;
            string json = new UTF8Encoding(false, true).GetString(frame);
            CheckMembers(json);
            Dictionary<string, object> request = Json.Deserialize<Dictionary<string, object>>(json);
            Number(request, "version", 1, 1);
            string id = Text(request, "request_id", 64);
            if (!Regex.IsMatch(id, "^[A-Za-z0-9_-]+$")) return 2;
            string vehicle = Text(request, "vehicle", 128), ecu = Text(request, "ecu", 128);
            int level = Number(request, "level", 1, 127), size = Number(request, "output_size", 1, 64);
            Number(request, "timeout_ms", 1, 30000);
            string hex = Text(request, "seed_hex", 128);
            if (!Regex.IsMatch(hex, "^(?:[0-9a-fA-F]{2})+$")) return 2;
            byte[] seed = new byte[hex.Length / 2];
            for (int i = 0; i < seed.Length; i++) seed[i] = Convert.ToByte(hex.Substring(i * 2, 2), 16);
            byte[] prefix = Encoding.UTF8.GetBytes("V-CODE M05B TEST ONLY\0" + vehicle + "\0" + ecu);
            byte[] material = new byte[prefix.Length + 1 + seed.Length];
            Buffer.BlockCopy(prefix, 0, material, 0, prefix.Length);
            material[prefix.Length] = (byte)level;
            Buffer.BlockCopy(seed, 0, material, prefix.Length + 1, seed.Length);
            byte[] digest;
            using (SHA256 sha = SHA256.Create()) digest = sha.ComputeHash(material);
            StringBuilder key = new StringBuilder();
            for (int i = 0; i < size; i++) key.Append(digest[i % digest.Length].ToString("x2"));
            byte[] output = Encoding.ASCII.GetBytes(Json.Serialize(new {
                version = 1, request_id = id, status = "ok", key_hex = key.ToString(), mock_only = true }));
            Stream stream = Console.OpenStandardOutput();
            stream.Write(BitConverter.GetBytes(output.Length), 0, 4);
            stream.Write(output, 0, output.Length);
            stream.Flush();
            Array.Clear(seed, 0, seed.Length);
            Array.Clear(material, 0, material.Length);
            Array.Clear(digest, 0, digest.Length);
            Array.Clear(frame, 0, frame.Length);
            return 0;
        }
        catch { return 2; } // Never echo input, secrets, paths or native exception text.
    }
}
