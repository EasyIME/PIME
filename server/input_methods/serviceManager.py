import os
import threading

class IMServiceManager:
    def __init__(self):
        self.__lock = threading.Lock()
        self.dicService2CtorHookInfo = {}
        self.__enumerateServices()

    def __enumerateServices(self):
        # To enumerate currently installed Input Method

        def getModuleServiceNameFromJSON(jsonFile):
            import json
            # Read the moduleName(xxx.py) & serviceName(class name) from JSON
            jsonData = None
            with open(jsonFile) as dataFile:
                jsonData = json.load(dataFile)
            if not jsonData:
                return "", ""
            moduleName = jsonData.get("moduleName", "")
            serviceName = jsonData.get("serviceName", "")
            return moduleName, serviceName

        import importlib
        currentDir = os.path.dirname(os.path.abspath(__file__))
        for root, dirs, files in os.walk(currentDir):
            for filename in files:
                if filename.lower().endswith(".json"):
                    absPath = os.path.join(root, filename)
                    moduleName, serviceName = getModuleServiceNameFromJSON(absPath)
                    if not moduleName or not serviceName:
                        continue

                    # Import target im module and store class constructor for
                    # later instantiation.
                    relativeModulePath = os.path.relpath(os.path.join(root, moduleName))
                    module_name = relativeModulePath.replace(os.sep , ".")
                    module_ = importlib.import_module(module_name)
                    class_ = getattr(module_, serviceName)
                    self.dicService2CtorHookInfo[serviceName] = { "class" : class_,
                                                                  "hooked" : False}

    def getNumOfServices(self):
        return len(self.dicService2CtorHookInfo)

    def pickOneServiceAndMarkHooked(self, client):
        # For Client creation, pick one im service for single client and mark
        # |'hooked' = True| in order to avoid duplicately using.
        with self.__lock:
            for service, info in self.dicService2CtorHookInfo.iteritems():
                if not info["hooked"]:
                    serviceInstance = info["class"](client)
                    self.dicService2CtorHookInfo[service]["hooked"] = True
                    return serviceInstance
        return None

IMServiceMgr = IMServiceManager()
