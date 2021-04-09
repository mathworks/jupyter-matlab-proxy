# Copyright 2020 The MathWorks, Inc.

import os, pytest, signal, psutil
from jupyter_matlab_proxy import settings
from subprocess import Popen, PIPE



def pytest_generate_tests(metafunc):
    os.environ["DEV"] = "true"


@pytest.fixture(autouse=True, scope='session')
def pre_test_cleanup():
    """A pytest fixture which deletes matlab_config_file before executing tests.
    
    If a previous pytest run fails, this file may have an empty Dict which leads
    to the server never starting up matlab.
    """
       
    try:
        matlab_config_file = settings.get(dev = True)['matlab_config_file']
        os.remove(matlab_config_file)
    except:
        pass

@pytest.fixture(name='mock_settings_get_custom_ready_delay')
def mock_settings_get_custom_ready_delay_fixture(mocker): 
    """A pytest fixture which mocks settings.get() method.
    
    The ready_delay for the fake_matlab_process is 10 (by default)
    The 'matlab_cmd' returned within settings.get() method does not
    contain a --ready-delay option for running the command. So it defaults to 10.
     
    This fixture mocks the settings.get() method and then modifies only the 
    'matlab_cmd' key.
    
    It adds the --ready-delay param and sets its value to 0.

    Args:
        mocker : A built in pytest fixture
        dev_settings (Dict): A Dict which contains dev-mode settings 
    """
    
    #Grab the settings:
    custom_settings = settings.get(dev=True)
    
    # Add the --ready-delay param with value 0
    ready_delay = ['--ready-delay', '0']    
    matlab_cmd = custom_settings['matlab_cmd']      
    matlab_cmd[4:4] = ready_delay  
    
    #Update the matlab_cmd key
    custom_settings['matlab_cmd'] = matlab_cmd
    
    #Patch it to return the custom settings.
    mocker.patch('jupyter_matlab_proxy.settings.get', return_value=custom_settings)    
