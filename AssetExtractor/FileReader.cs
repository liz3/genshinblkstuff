﻿using System.IO;
using System.Linq;

namespace AssetStudio
{
    public class FileReader : EndianBinaryReader
    {
        public string FullPath;
        public string FileName;
        public FileType FileType;
        public long Length;

        public FileReader(string path) : this(path, File.Open(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite)) { }

        public FileReader(string path, Stream stream) : base(stream, EndianType.BigEndian)
        {
            FullPath = Path.GetFullPath(path);
            FileName = Path.GetFileName(path);
            FileType = CheckFileType();
            Length = stream.Length;
        }

        private FileType CheckFileType()
        {
            var signature = this.ReadStringToNull(20);
            Position = 0;
            switch (signature)
            {
                case "UnityWeb":
                case "UnityRaw":
                case "UnityArchive":
                case "UnityFS":
                    return FileType.BundleFile;
                case "UnityWebData1.0":
                    return FileType.WebFile;
                case "blk":
                    return FileType.BlkFile;
                default:
                    {
                        var magic = ReadBytes(2);
                        Position = 0;
                
                        Position = 0x20;
                        magic = ReadBytes(6);
                        Position = 0;
                 
                        if (IsSerializedFile())
                        {
                            return FileType.AssetsFile;
                        }
                        else
                        {
                            return FileType.ResourceFile;
                        }
                    }
            }
        }

        private bool IsSerializedFile()
        {
            var fileSize = BaseStream.Length;
            if (fileSize < 20)
            {
                return false;
            }
            var m_MetadataSize = ReadUInt32();
            long m_FileSize = ReadUInt32();
            var m_Version = ReadUInt32();
            long m_DataOffset = ReadUInt32();
            var m_Endianess = ReadByte();
            var m_Reserved = ReadBytes(3);
            if (m_Version >= 22)
            {
                if (fileSize < 48)
                {
                    Position = 0;
                    return false;
                }
                m_MetadataSize = ReadUInt32();
                m_FileSize = ReadInt64();
                m_DataOffset = ReadInt64();
            }
            Position = 0;
            // ???
            if (m_FileSize != fileSize)
            {
                //return false;
            }
            if (m_DataOffset > fileSize)
            {
                return false;
            }
            return true;
        }
    }
}
