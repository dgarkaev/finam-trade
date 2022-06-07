from ctypes import *
import platform
import os

XC_ENCODING = 'utf-8'


def c_str(string):
    """Create ctypes char * from a Python string.

    Parameters
    ----------
    string : string type
        Python string.

    Returns
    -------
    str : c_char_p
        A char pointer that can be passed to C API.

    Examples
    --------
    >>> x = mx.base.c_str("Hello, World")
    >>> print(x.value)
    b"Hello, World"
    """
    return c_char_p(string.encode('utf-8'))


class XmlConnector:
    def __init__(self):
        self.__callback = None
        self.__ucallback = None
        path = os.path.abspath(os.path.dirname(__file__))
        self.lib = WinDLL(os.path.join(path, 
                          "txmlconnector64.dll" if platform.machine() == 'AMD64' 
                          else 'txmlconnector.dll'))
        # self.lib = windll.LoadLibrary(path)
        print(self.lib)
        self.__SetFunctions()
        self.__SetCallback(self.__xcallback)

    def Initialize(self, log_path='./logs', log_level=2):
        # res = self.func_init(log_path.encode(XC_ENCODING), log_level)
        res = self.func_init(c_str(log_path), log_level)
        py_res = cast(res, c_char_p).value
        if (res != None):
            py_res = py_res.decode(XC_ENCODING)
            self.func_free_mem(res)
        return py_res

    def InitializeEx(self, log_path='./logs', log_level=2):
        xml = f'<init log_path = "{log_path}" log_level="{log_level}" logfile_lifetime=""/>'
        res = self.func_init_ex(c_str(xml))
        py_res = cast(res, c_char_p).value
        if (res != None):
            py_res = py_res.decode(XC_ENCODING)
            self.func_free_mem(res)
        return py_res

    def UnInitialize(self):
        res = self.func_uninit()
        py_res = cast(res, c_char_p).value
        if (res != None):
            py_res = py_res.decode(XC_ENCODING)
            self.func_free_mem(res)
        return py_res

    def SendCommand(self, command):
        res = self.func_send_cmd(command.encode(XC_ENCODING))
        py_res = cast(res, c_char_p).value
        if (res != None):
            py_res = py_res.decode(XC_ENCODING)
            self.func_free_mem(cast(res, POINTER(c_long)))
        return py_res

    def SetUserCallback(self, fun):
        self.__ucallback = fun

    def __SetFunctions(self):
        self.func_init = self.lib.Initialize
        self.func_init.argtypes = [c_char_p, c_int]
        self.func_init.restype = c_void_p

        self.func_init_ex = self.lib.InitializeEx
        self.func_init_ex.argtypes = [c_char_p]
        self.func_init_ex.restype = c_void_p

        self.func_uninit = self.lib.UnInitialize
        self.func_uninit.restype = c_void_p
        self.func_set_callback = self.lib.SetCallback
        self.func_set_callback.restype = c_bool
        self.func_send_cmd = self.lib.SendCommand
        self.func_send_cmd.restype = c_void_p
        self.func_free_mem = self.lib.FreeMemory
        self.func_free_mem.restype = c_bool
        self.func_service_info = self.lib.GetServiceInfo
        self.func_service_info.restype = c_int

    def __SetCallback(self, func):
        prototype = WINFUNCTYPE(c_bool, POINTER(c_ubyte))
        self.__callback_func = prototype(self.__xcallback)
        res = self.func_set_callback(self.__callback_func)
        if (not res):
            print("Failed to set callback")

    def __xcallback(self, data):
        # breakpoint()
        if (not self.__ucallback == None):
            # кому надо - сам декодирует из BYTE в UTF-8 STRING
            py_data = cast(data, c_char_p).value  # .decode(XC_ENCODING)
            self.__ucallback(py_data)
        self.func_free_mem(data)
        return 0

    def GetServiceInfo(self, request):
        """
        1.1 Функция GetServiceInfo
        """
        response = c_char_p()
        ret_code = self.func_service_info(
            request.encode(XC_ENCODING), pointer(response))
        res = "Not privided by xmlconnector"
        if not response.value == None:
            res = response.value.decode(XC_ENCODING)
            self.func_free_mem(response)
        return ret_code, res
