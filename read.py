import io
from struct import *
import sys
def readString(myfile):
    chars = []
    while True:
        c = myfile.read(1)
        if c == b'\x00':
            return "".join(chars)
        chars.append(c.decode('ascii'))
def reade(f, header, fmt):
  fnl = "<" if header["endianess"] == 0 else ">"
  fnl += fmt
  return unpack(fnl, f.read(calcsize(fnl)))[0]
def type_tree_blob_read(f, header, t):
    number_of_nodes = reade(f, header, "i")
    string_buffer_size = reade(f, header, "i")
    nodes = []
    for i in range(number_of_nodes):
        node = {
            "version": reade(f, header, "H"),
            "level": reade(f, header, "B"),
            "type_flags": reade(f, header, "B"),
            "type_str_offset": reade(f, header, "I"),
            "name_str_offset": reade(f, header, "I"),
            "byte_size": reade(f, header, "i"),
            "index": reade(f, header, "i"),
            "meta_flag": reade(f, header, "i"),
        }
        if header["version"] >= 19:
            node["ref_type_hash"] = reade(f, header, "Q")
        nodes.append(node)
    string_buffer = f.read(string_buffer_size)
    reader = io.BytesIO(string_buffer)
    def i_read_str(reader, value):
        is_offset = (value & 0x80000000) == 0
        if is_offset:
            reader.seek(value)
            return readString(reader)
        offset = value & 0x7FFFFFFF
        return str(offset)
    for x in range(number_of_nodes):
        node = t["nodes"][x]
        nodes[x]["type"] = i_read_str(reader, node["type_str_offset"])
        nodes[x]["name"] = i_read_str(reader, node["name_str_offset"])
    return nodes
def read_type_tree(f, header, t, level = 0):
    node = t
    if t == None:
        node = {
            "level": level,
            "type": readString(f),
            "name": readString(f),
            "byte_size": reade(f, header, "i"),
            "childs": []
        }
    if header["version"] == 2:
        count = reade(f, header, "i")
    if header["version"] != 3:
        node["indec"] = reade(f, header, "i")
    node["type_flags"] = reade(f, header, "i")
    node["version"] = reade(f, header, "i")
    if header["version"] != 3:
        node["meta_flag"] = reade(f, header, "i")
    childCount = reade(f, header, "i")
    for x in range(childCount):
        node["childs"].append(read_type_tree(f, header, node, level+1))
    return node
def read_serialised_type(f, header):
    buf = f.read(4)
    buf = bytes([c for t in zip(buf[1::2], buf[::2]) for c in t])
    type_state = {
        "script_type_index": -1
    }
    type_state["class_id"] = (unpack("i", buf)[0] ^ 0x23746FBE) -3
    if header["version"] >= 16:
        type_state["is_stripped_type"] = reade(f, header, "?")
    if header["version"] >= 17:
        type_state["script_type_index"] = reade(f, header, "h")
    if header["version"] >= 13:
        if type_state["script_type_index"] >= 0:
            type_state["script_id"] = f.read(16)
        elif (header["version"] < 16 and type_state["class_id"] < 0) or (header["version"] >= 16 and type_state["class_id"] == 114):
            type_state["script_id"] = f.read(16)
        type_state["old_type_hash"] = f.read(16)
    if header["enable_type_tree"]:
        type_state["m_type"] = {}
        if header["version"] >= 12 or header["version"] == 10:
            type_state["m_type"]["nodes"] = type_tree_blob_read(f, header, type_state)
        else:
            type_state["m_type"]["nodes"] = read_type_tree(f, header, None)
    return type_state
with open(sys.argv[1], "rb") as f:
    header = {
        "metadata_size": unpack(">I", f.read(4))[0],
        "f_size": unpack(">I", f.read(4))[0],
        "version": unpack(">I", f.read(4))[0],
        "data_offset": unpack(">I", f.read(4))[0]
    }
    if header["version"] >= 9:
        header["endianess"] = unpack("B", f.read(1))[0]
        header["m_reserved"] = f.read(3)
    else:
        f.seek(header["f_size"] - header["metadata_size"])
        header["endianess"] = unpack("B", f.read(1))[0]
    if header["version"] >= 7:
        header["unity_version"] = readString(f)
    if header["version"] >= 8:
        header["target_platform"] = reade(f, header, "i")
    if header["version"] >= 13:
        header["enable_type_tree"] = reade(f, header, "?")
    print(header)
    type_count = reade(f, header, "i")
    header["types"] = []
    for x in range(type_count):
        header["types"].append(read_serialised_type(f, header))
    if header["version"] >= 7 and header["version"] < 14:
        header["big_id_enabled"] = reade(f, header, "i")
    object_count = reade(f, header, "i")
    for x in range(object_count):
        o = {
            path_id: reade(f, header, "q")
        }
        if header["version"] >= 22:
            o["byte_start"] = reade(f, header, "q")
        else:
            o["byte_start"] = reade(f, header, "i")
        o["byte_start"] += header["data_offset"]
        o["byte_size"] = reade(f, header, "I")
        o["type_id"] = reade(f, header, )
