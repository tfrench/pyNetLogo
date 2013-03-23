'''
Created on 21 mrt. 2013

.. codeauthor:: jhkwakkel <j.h.kwakkel (at) tudelft (dot) nl>

'''
import jpype
import os

__all__ = ['NetLogoException',
           'NetLogo',
           'NETLOGO_HOME',
           'PYNETLOGO_HOME']

NETLOGO_HOME = r'C:/Program Files (x86)/NetLogo 5.0.3'
PYNETLOGO_HOME = os.path.dirname(os.path.abspath(__file__))

class NetLogoException(Exception):
    '''
    
    wrapper around the netlogo java exceptions. As message it contains
    the message of the java exception
    
    '''
    
    pass

class NetLogo():
    ''' interface to netlogo'''
    
    
    def __init__(self, gui=False, thd=False):
        '''
        
        Create a link with netlogo. Underneath, the netlogo jvm is started
        through jpype.
        
        
        :param gui: boolean, if true run netlogo with gui, otherwise run in 
                    headless mode. Defaults to false.
        :param thd: boolean, if thrue start netlogo in 3d mode. Defaults to 
                    false
        
        
        '''
        if not jpype.isJVMStarted():
            # netlogo jars
            jars = [NETLOGO_HOME + r'/lib/scala-library.jar',
                    NETLOGO_HOME + r'/lib/asm-all-3.3.1.jar',
                    NETLOGO_HOME + r'/lib/picocontainer-2.13.6.jar',
                    NETLOGO_HOME + r'/lib/log4j-1.2.16.jar',
                    NETLOGO_HOME + r'/lib/jmf-2.1.1e.jar',
                    NETLOGO_HOME + r'/lib/pegdown-1.1.0.jar',
                    NETLOGO_HOME + r'/lib/parboiled-core-1.0.2.jar',
                    NETLOGO_HOME + r'/lib/parboiled-java-1.0.2.jar',
                    NETLOGO_HOME + r'/lib/mrjadapter-1.2.jar',
                    NETLOGO_HOME + r'/lib/jhotdraw-6.0b1.jar',
                    NETLOGO_HOME + r'/lib/quaqua-7.3.4.jar',
                    NETLOGO_HOME + r'/lib/swing-layout-7.3.4.jar',
                    NETLOGO_HOME + r'/lib/jogl-1.1.1.jar',
                    NETLOGO_HOME + r'/lib/gluegen-rt-1.1.1.jar',
                    NETLOGO_HOME + r'/NetLogo.jar',
                    PYNETLOGO_HOME + r'/java/netlogoLink.jar']
            
            # format jars in right format for starting java virtual machine
            jars = ";".join(jars)
            jarpath = '-Djava.class.path={}'.format(jars)
            jvm_dll = NETLOGO_HOME + r'/jre/bin/client/jvm.dll'            
            jpype.startJVM(jvm_dll, jarpath, "-Xmx1024m")

        a = jpype.java.lang.System.getProperty("java.library.path")
        
        # for some reason, netlogo 3d has hardcoded refs to the 
        # jogl.dll etc. So, we change the current working directory of the
        # jvm to the home directory of netlogo.
        # NOTE:: this means that the current working directory of python
        # and netlogo are NOT the same
        jpype.java.lang.System.setProperty('user.dir', NETLOGO_HOME)
     
        link = jpype.JClass('netlogoLink.NetLogoLink')
        self.link = link(gui, thd)
        
            
    def load_model(self, path):
        '''
        
        load a netlogo model.
        
        :param path: the absolute path to the netlogo model
        :raise: IOError in case the  model is not found
        :raise: NetLogoException 
        
        '''
        try:
            self.link.loadModel(path)
        except jpype.JException(jpype.java.io.IOException)as ex:
            raise IOError(ex.message())
        except jpype.JException(jpype.java.org.nlogo.api.LogoException) as ex:
            raise NetLogoException(ex.message())
        except jpype.JException(jpype.java.org.nlogo.api.CompilerException) as ex:
            raise NetLogoException(ex.message())
        except jpype.JException(jpype.java.lang.InterruptedException) as ex:
            raise NetLogoException(ex.message())



    def kill_workspace(self):
        '''
        
        close netlogo. Note that the jvm keeps running. At the moment
        you will need to restart your python session if you would like
        to create a new link to netlogo.
        
        '''
        
        self.link.killWorkspace()

        
    def command(self, netlogo_command):
        '''
        
        Execute the supplied command in netlogo
        
        :param netlogo_command: a string with a valid netlogo command
        :raises: NetLogoException in case of either a LogoException or 
                 CompilerException being raised by netlogo.
        
        '''
        
        try:
            self.link.command(netlogo_command)
        except jpype.JException(jpype.java.org.nlogo.api.LogoException) as ex:
            raise NetLogoException(ex.message())
        except jpype.JException(jpype.java.org.nlogo.api.CompilerException) as ex:
            raise NetLogoException(ex.message())

    def report(self, netlogo_reporter):
        '''
        
        Every reporter (commands which return a value) that can be called in 
        the NetLogo Command Center can be called with this method.
        
        :param netlogo_reporter: a valid netlogo reporter 
        :raises: NetlogoException
        
        '''
        
        try:
            result = self.link.report(netlogo_reporter)
            return self._cast_results(result)
        except jpype.JException(jpype.java.org.nlogo.api.LogoException) as ex:
            raise NetLogoException(ex.message())
        except jpype.JException(jpype.java.org.nlogo.api.CompilerException) as ex:
            raise NetLogoException(ex.message()) 
        except jpype.JException(jpype.java.lang.Exception) as ex:
            raise NetLogoException(ex.message()) 


    def _cast_results(self, results):
        '''
        
        Convert the results to the proper python data type. The java NLResults
        class knows the datatype for the results it contains and has converter 
        methods for each. This method relies on the fact that jpype will
        convert java primitives (e.g. int, boolean, double) to the right python 
        datatype. 
        
        :param results; the results from report
        :returns: a correct python version of the results
        
        .. note:: netlogo extension datatypes like array are currently not 
                  supported.
        
        '''
        
        java_dtype = results.type
        
        if java_dtype == "Boolean":
            results = results.getResultAsBoolean()
            if results == 1:
                return True
            else:
                return False
        elif java_dtype == "String":
            return results.getResultAsString()       
        elif java_dtype == "Integer":
            return results.getResultAsInteger()
        elif java_dtype == "Double":
            return results.getResultAsDouble()
        elif java_dtype == "BoolList":
            results = results.getResultAsBooleanArray()
            
            tr = []
            for entry in results:
                if entry == 1:
                    tr.append(True)
                else:
                    tr.append(False)
            return tr
        elif java_dtype == "StringList":
            return results.getResultAsStringArray()   
        elif java_dtype == "IntegerList":
            return results.getResultAsIntegerArray() 
        elif java_dtype == "DoubleList":
            return results.getResultAsDoubleArray() 
        else:
            raise NetLogoException("unknown datatype")