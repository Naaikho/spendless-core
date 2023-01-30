import sys, os
import datetime
import json
import uuid
import platform
from base64 import b64decode as bdec, b64encode as benc
# import logging as log
import pyflp_cstm
import traceback
import io
from typing import Union

def transformSys():
    """ Returns the path where the executed file is located """
    if getattr(sys, 'frozen', False):
        path = os.path.dirname(sys.executable)
    elif __file__:
        path = os.path.dirname(__file__)
    return path

# fix the wrong path of sys.path[0]
sys.path[0] = transformSys()

class FlParser():
    """ Minimized class for pyflp parsing and optimized for SpendLess """

    # init with super class
    def __init__(self, f:Union[bytes, str], projectBaseDir:str=None):
        try:
            # logs dir path
            self._LOGS = self._nkPath(sys.path[0], 'logs')

            # base dir of the project
            self._project_dir = projectBaseDir

            # /logs
            # create logs dir if not exists
            if not os.path.exists(self._LOGS):
                os.mkdir(self._LOGS)
            
            self._pj = None
            # if f is bytes, parse
            if(isinstance(f, bytes)):
                self._pj = pyflp_cstm.parse(io.BytesIO(f))
            # if f is str, read the path and parse
            elif isinstance(f, str):
                f = io.BytesIO(open(f, 'rb').read())
                self._pj = pyflp_cstm.parse(f)
            else:
                raise TypeError("f must be bytes or str")
        except:
            self._NkLog(traceback.format_exc())
            raise Exception("Error while parsing the file")
    


    def getInfos(self, hardData:bool=False):
        try:
            dt = {}
            # title
            dt["title"] = self._pj.title
            # artist
            dt["artist"] = self._pj.artists
            # description
            dt["description"] = self._pj.comments
            # genre
            dt["genre"] = self._pj.genre
            # version
            dt["version"] = str(self._pj.version)
            # tempo
            dt["tempo"] = float(str(self._pj.tempo))
            # createdAt
            dt["createdAt"] = self._pj.created_on.timestamp()
            # workTime
            dt["workTime"] = self._pj.time_spent.total_seconds()
            # samples
            dt["samples"] = []
            # plugins
            dt["plugins"] = []

            # tmpHist stack already added plugins
            tmpHist = []

            # enum channels
            for c in self._pj.channels:
                # if the channel not a sampler or instrument, continue
                if not isinstance(c, pyflp_cstm.channel.Sampler) and not isinstance(c, pyflp_cstm.channel.Instrument):
                    continue
                # if the channel is a sampler and have a sample path, add it to samples list
                if isinstance(c, pyflp_cstm.channel.Sampler) and c.sample_path:
                    dt["samples"].append(str(c.sample_path))
                # if the channel is an instrument and have a plugin, add it to plugins list
                if isinstance(c, pyflp_cstm.channel.Instrument):
                    try:
                        # if the plugin is not already added, add it
                        if c.plugin.name not in tmpHist:
                            dt["plugins"].append({
                                "name": c.plugin.name,
                                "by": c.plugin.vendor,
                            })
                            tmpHist.append(c.plugin.name)
                    except:
                        pass
        
            return (json.dumps(dt) if not hardData else dt)
        except:
            self._NkLog(traceback.format_exc())
            raise Exception("Error while getting infos")

    def setInfos(self, dt:dict) -> None:
        try:
            # title
            if("title" in dt.keys()):
                self._pj.title = str(dt["title"])
            # artist
            if("artist" in dt.keys()):
                self._pj.artists = str(dt["artist"])
            # description
            if("description" in dt.keys()):
                self._pj.comments = str(dt["description"])
            # genre
            if("genre" in dt.keys()):
                self._pj.genre = str(dt["genre"])
            # tempo
            if("tempo" in dt.keys()):
                self._pj.tempo = float(str(dt["tempo"]))

            # enum channels
            for ind, c in enumerate(self._pj.channels):
                # if the channel not a sampler or instrument, continue
                if not isinstance(c, pyflp_cstm.channel.Sampler) and not isinstance(c, pyflp_cstm.channel.Instrument):
                    continue
                # if the channel is a sampler and have a sample path, edit path to sample dir
                if isinstance(c, pyflp_cstm.channel.Sampler) and c.sample_path and self._project_dir:
                    self._pj.channels[ind].sample_path = self._nkPath(self._project_dir, "samples", str(c.sample_path).replace("\\", "/").split("/")[-1]).replace("\\", "/")
        except:
            self._NkLog(traceback.format_exc())
            raise Exception("Error while setting infos")
    
    def setSamples(self) -> None:
        try:
            # enum channels
            for ind, c in enumerate(self._pj.channels):
                # if the channel not a sampler or instrument, continue
                if not isinstance(c, pyflp_cstm.channel.Sampler) and not isinstance(c, pyflp_cstm.channel.Instrument):
                    continue
                # if the channel is a sampler and have a sample path, edit path to sample dir
                if isinstance(c, pyflp_cstm.channel.Sampler) and c.sample_path and self._project_dir:
                    self._pj.channels[ind].sample_path = self._nkPath(self._project_dir, "samples", str(c.sample_path).replace("\\", "/").split("/")[-1]).replace("\\", "/")
        except:
            self._NkLog(traceback.format_exc())
            raise Exception("Error while set samples")
    
    def export(self, infos:bool=False, byte:bool=False) -> Union[bytes, str]:
        try:
            if not infos:
                return json.dumps({
                    "file": (pyflp_cstm.save(self._pj, byte=True) if byte else benc(pyflp_cstm.save(self._pj, byte=True)).decode())
                })
            else:
                exp = self.getInfos(True)
                exp["file"] = (pyflp_cstm.save(self._pj, byte=True) if byte else benc(pyflp_cstm.save(self._pj, byte=True)).decode())
                return json.dumps(exp)
        except:
            self._NkLog(traceback.format_exc())
            raise Exception("Error while exporting file")
        
    


    def _nkPath(self, *args) -> str:
        """ Return `path` in args as a string. """
        p = args[0]
        for a in args[1:]:
            p = os.path.join(p, a)
        return p
    
    def _NkLog(self, *msg):
        tmp = []
        for m in msg:
            tmp.append(str(m))
        msg = " ".join(tmp)
        with open(self._nkPath(self._LOGS, "app.log"), "a") as f:
            f.write(msg + "\n")

if not os.path.exists(os.path.join(sys.path[0], "tmp")):
    os.mkdir(os.path.join(sys.path[0], "tmp"))

def writeInTmpFile(data:str) -> None:
    fileId = str(uuid.uuid4())
    with open(os.path.join(sys.path[0], "tmp", "." + fileId), "w") as f:
        f.write(data)
    return str(os.path.join(sys.path[0], "tmp", "." + fileId))

try:
    cmd = sys.argv[1]
except:
    print("Please provide a command")
    sys.stdout.flush()
    sys.exit(1)

if cmd not in ["info", "export", "set", "samples"]:
    print("Invalid command")
    sys.stdout.flush()
    sys.exit(1)

try:
    file = sys.argv[2]
except:
    print("Please provide a file path")
    sys.stdout.flush()
    sys.exit(1)

try:
    project_dir = sys.argv[3]
except:
    print("Please provide a project dir")
    sys.stdout.flush()
    sys.exit(1)

if not file.endswith(".flp"):
    try:
        file = bdec(file.encode())
    except:
        print("Invalid file")
        sys.stdout.flush()
        sys.exit(1)

flp = None
try:
    flp = FlParser(file, project_dir)
except Exception as e:
    print("Error while parsing the file: " + str(e))
    sys.stdout.flush()
    sys.exit(1)



if not flp:
    print("Error while parsing the file")
    sys.stdout.flush()
    sys.exit(1)

if cmd == "info":
    print(writeInTmpFile(flp.getInfos()))

if cmd == "set":
    try:
        data = json.loads(bdec(sys.argv[4]))
    except:
        print("Please provide json data to 'set' command")
        sys.stdout.flush()
        sys.exit(1)
    try:
        flp.setInfos(data)
        print(writeInTmpFile(flp.export(True)))
    except Exception as e:
        print("Error while setting infos: " + str(e))
        sys.stdout.flush()
        sys.exit(1)

if cmd == "samples":
    try:
        flp.setSamples()
        print(writeInTmpFile(flp.export()))
    except Exception as e:
        print("Error while setting infos: " + str(e))
        sys.stdout.flush()
        sys.exit(1)

if cmd == "export":
    print(writeInTmpFile(flp.export()))

sys.stdout.flush()