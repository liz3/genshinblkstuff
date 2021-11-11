import json
from os import listdir
from os.path import isfile, join
import io
from struct import *
import sys
from PIL import Image

def readString(myfile):
    chars = []
    while True:
        c = myfile.read(1)
        if c == b'\x00':
            return "".join(chars)
        chars.append(c.decode('ascii'))
def align(f):
    curr = f.tell()
    mod = curr % 4
    if mod != 0:
        f.seek(4-mod, 1)
def read_string_aligned(stream, header):
    length = reade(stream, header, "i")
    if length > 0:
        buf = stream.read(length)
        res = buf.decode("utf-8")
        align(stream)
        return res
    return ""
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
        node = nodes[x]
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
def read_serialised_type(f, header, is_ref_type):
    buf = bytearray(f.read(4))
    buf.reverse()
    buf = bytes(buf)

    type_state = {
        "script_type_index": -1
    }
    type_state["class_id"] = (unpack("i", buf)[0] ^ 0x23746FBE) -3
    if header["version"] >= 16:
        type_state["is_stripped_type"] = reade(f, header, "?")
    if header["version"] >= 17:
        type_state["script_type_index"] = reade(f, header, "h")
    if header["version"] >= 13:
        if type_state["script_type_index"] >= 0 and is_ref_type:
            type_state["script_id"] = str(f.read(16))
        elif (header["version"] < 16 and type_state["class_id"] < 0) or (header["version"] >= 16 and type_state["class_id"] == 114):
            type_state["script_id"] = str(f.read(16))
        type_state["old_type_hash"] = str(f.read(16))
    if header["enable_type_tree"]:
        type_state["m_type"] = {}
        if header["version"] >= 12 or header["version"] == 10:
            type_state["m_type"]["nodes"] = type_tree_blob_read(f, header, type_state)
        else:
            type_state["m_type"]["nodes"] = read_type_tree(f, header, None)
        if header["version"] >= 21:
            if is_ref_type:
                type_state["klass_name"] = readString(f)
                type_state["namespace"] = readString(f)
                type_state["asm_name"] = readString(f)
            else:
                count = reade(f, header, "i")
                type_state["type_dependencies"] = []
                for x in range(count):
                    type_state["type_dependencies"].append(reade(f, header, "i"))
    return type_state
def read_file(path):
    with open(path, "rb") as f:
        header = {
            "metadata_size": unpack(">I", f.read(4))[0],
            "f_size": unpack(">I", f.read(4))[0],
            "version": unpack(">I", f.read(4))[0],
            "data_offset": unpack(">I", f.read(4))[0]
        }
        if header["version"] >= 9:
            header["endianess"] = unpack("B", f.read(1))[0]
            header["m_reserved"] = str(f.read(3))
        else:
            f.seek(header["f_size"] - header["metadata_size"])
            header["endianess"] = unpack("B", f.read(1))[0]
        if header["version"] >= 7:
            header["unity_version"] = readString(f)
            header["unity_version_parts"] = [2017, 4, 30, 1, 2]
            # for p in header["unity_version"].split("."):
            #     header["unity_version_parts"].append(int(p))
        if header["version"] >= 8:
            header["target_platform"] = reade(f, header, "i")
        if header["version"] >= 13:
            header["enable_type_tree"] = reade(f, header, "?")
        type_count = reade(f, header, "i")
        header["types"] = []
        for x in range(type_count):
            header["types"].append(read_serialised_type(f, header, False))
        if header["version"] >= 7 and header["version"] < 14:
            header["big_id_enabled"] = reade(f, header, "i")
        else:
            header["big_id_enabled"] = 0
        object_count = reade(f, header, "i")
        objs = []
        for x in range(object_count):
            o = {
            }
            if header["big_id_enabled"] != 0:
                o["path_id"] = reade(f, header, "q")
            elif header["version"] < 14:
                o["path_id"] = reade(f, header, "i")
            else:
                align(f)
                o["path_id"] = reade(f, header, "q")
            if header["version"] >= 22:
                o["byte_start"] = reade(f, header, "q")
            else:
                o["byte_start"] = reade(f, header, "I")
            o["byte_start"] += header["data_offset"]
            o["byte_size"] = reade(f, header, "I")
            o["type_id"] = reade(f, header, "i")
            if header["version"] < 16:
                o["class_id"] = reade(f, header, "H")
                o["serialised_type"] = "TODO"
            else:
                o["serialised_type"] = header["types"][o["type_id"]]
                o["class_id"] = o["serialised_type"]["class_id"]
            if header["version"] < 11:
                o["is_destroyed"] = reade(f, header, "H")
            if header["version"] >= 11 and header["version"] < 17:
                o["script_type_index"] = reade(f, header, "h")
            if header["version"] == 15 or header["version"] == 16:
                o["stripped"] = str(f.read(1))
            objs.append(o)
        if header["version"] >= 11:
            count = reade(f, header, "i")
            header["script_types"] = []
            for x in range(count):
                o = {}
                o["local_serialised_file_index"] = reade(f, header, "i")
                if header["version"] < 14:
                    o["identifier_in_file"] = reade(f, header, "i")
                else:
                    align(f)
                    o["identifier_in_file"] = reade(f, header, "q")
                header["script_types"].append(o)
        header["objects"] = objs
        external_count = reade(f, header, "i")
        header["externals"] = []
        for x in range(external_count):
            external = {}
            if header["version"] >= 6:
                readString(f)
            if header["version"] >= 5:
                external["guid"] = str(f.read(16))
                external["type"] = reade(f, header, "i")
            external["path_name"] = readString(f)
            #        if "CAB~" in external["path_name"].upper():
            header["externals"].append(external)
        if header["version"] >= 20:
            header["ref_types"] = []
            refCount = reade(f, header, "i")
            for x in range(refCount):
                header["ref_types"].append(read_serialised_type(f, header, True))
        if header["version"] >= 5:
            header["user_information"] = readString(f)
        return header

def read_entry(path, offset, l):
    with open(path, "rb") as f:
        f.seek(offset)
        buf = f.read(l)
        return buf
def as_stream(buf):
    return io.BytesIO(buf)
def read_img(stream, header, f_path):
    stream.seek(0, 2)
    total_len = stream.tell()
    stream.seek(0)
    entry = {
        "name": read_string_aligned(stream, header)
    }
    v = header["unity_version_parts"]
    if header["unity_version_parts"][0] > 2017 or (header["unity_version_parts"][0] == 2017 and header["unity_version_parts"][1] >= 3):
        entry["forced_fallback_format"] = reade(stream, header, "i")
        entry["downscale_fallback"] = reade(stream, header, "?")
        if header["unity_version_parts"][0] > 2020 or (header["unity_version_parts"][0] == 2020 and header["unity_version_parts"][1] >= 2):
            entry["is_alpha_channel_optional"] = reade(stream, header, "?")
        align(stream)

    entry["width"] = reade(stream, header, "i")
    entry["height"] = reade(stream, header, "i")
    entry["complete_img_size"] = reade(stream, header, "i")
    if header["unity_version_parts"][0] >= 2020:
        reade(stream, header, "i")
    entry["format"] = reade(stream, header, "i")
    if header["unity_version_parts"][0] < 5 or (header["unity_version_parts"][0] == 5 and header["unity_version_parts"][1] < 2):
        entry["mip_map"] = reade(stream, header, "?")
    else:
        entry["mip_count"] = reade(stream, header, "i")
    if v[0] > 2 or (v[0] == 2 and v[1] >= 6):
        reade(stream, header, "?")
    if v[0] >= 2020:
        reade(streamm, header, "?")
    if v[0] > 2019 or (v[0] == 2019 and v[1] >= 3):
        reade(stream, header, "?")
    if v[0] >= 3 and (v[0] < 5 or (v[0] == 5 and v[1] < 4)):
        reade(stream, header, "?")
    if v[0] > 2018 or (v[0] == 2018 and v[1] >= 2):
        reade(stream, header, "?")
    align(stream)
    if v[0] > 2018 or (v[0] == 2018 and v[1] >= 2):
        reade(stream, header, "i")
    image_count = reade(stream, header, "i")
    texture_dimension = reade(stream, header, "i")
    # texture settings
    settings = {
        "filter_mode": reade(stream, header, "i"),
        "aniso": reade(stream, header, "i"),
        "mip_bias": reade(stream, header, "f"),
    }
    settings["wrap_mode"] = reade(stream, header, "i")
    if v[0] >= 2017:
        reade(stream, header, "i")
        reade(stream, header, "i")
    if v[0] >= 3:
        reade(stream, header, "i")
    if v[0] > 3 or (v[0] == 3 and v[1] >= 5):
        reade(stream, header, "i")
    if v[0] > 2020 or (v[0] == 2020 and v[1] >= 2):
        stream.read(reade(stream, header, "i"))
        align(stream)
    entry["settings"] = settings
    entry["image_size"] = reade(stream, header, "i")
    if entry["image_size"] == 0 and (v[0] > 5 or v[0] == 5 and v[1] >= 3):
        stream_info = {}
        stream_info["offset"] = reade(stream, header, "q") if v[0] >= 2020 else reade(stream, header, "I")
        stream_info["size"] = reade(stream, header, "I")
        stream_info["path"] = read_string_aligned(stream, header)
        entry["stream_info"] = stream_info
    if "stream_info" not in entry or len(entry["stream_info"]["path"]) == 0:
        img_data = stream.read(entry["image_size"])
        entry["img_data"] = img_data
    else:
        with open(f_path, "rb") as base_stream:
            base_stream.seek(0, 2)
            t_len = base_stream.tell()
            start = t_len - entry["complete_img_size"]
            base_stream.seek(start)
            img_data = base_stream.read(entry["complete_img_size"])
            entry["img_data"] = img_data

    return entry
path = sys.argv[1]

# {
#     "25": 7904,
#     "10": 603,
#     "4": 550,
#     "12": 375,
#     "1": 114,
#     "3": 34,
#     "24": 18,
#     "26": 12
# }

types={}
count=0
for folder in listdir(path):
    if isfile(join(path, folder)):
        continue
    for f in listdir(join(path, folder)):
        full_path = join(path, folder, f)
        if isfile(full_path):
            out = read_file(full_path)
            out["file_path"] = full_path
            # print(json.dumps(out, indent=4))
            for entry in out["objects"]:
                if entry["class_id"] == 28:
                    result = read_img(as_stream(read_entry(full_path, entry["byte_start"], entry["byte_size"])), out, full_path)
                    if result["format"] == 4 and "img_data" in result:
                        try:
                            img = Image.frombytes(mode="RGBA", data=result["img_data"], size=(result["width"], result["height"]))
                            img.save(join(sys.argv[2], str(count) + ".png"))
                        except ValueError:
                            pass
                    elif result["format"] == 25 and "img_data" in result:
                        with open(join(sys.argv[3], str(count) + ".bin"), "wb") as ff:
                            ff.write(pack("<I", result["width"]))
                            ff.write(pack("<I", result["height"]))
                            ff.write(result["img_data"])
                    count += 1
out = {k: v for k, v in sorted(types.items(), reverse=True, key=lambda item: item[1])}
print(json.dumps(out, indent=4))
