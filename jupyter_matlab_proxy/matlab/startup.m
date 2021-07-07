% Copyright 2020-2021 The MathWorks, Inc.

% Configure logged in user if possible
if ~isempty(getenv('MW_LOGIN_USER_ID'))
    user_id = getenv('MW_LOGIN_USER_ID');
    first_name = getenv('MW_LOGIN_FIRST_NAME');
    last_name = getenv('MW_LOGIN_LAST_NAME');
    email_address = getenv('MW_LOGIN_EMAIL_ADDRESS');
    profile_id = getenv('MW_LOGIN_PROFILE_ID');
    display_name = getenv('MW_LOGIN_DISPLAY_NAME');

    li = com.mathworks.matlab_login.MatlabLogin.isUserLoggedIn(2, 'DESKTOP');
    token = li.getToken();
    login_level = 2;
    remember_me = true;
    com.mathworks.matlab_login.MatlabLogin.saveCacheLoginInfo(first_name, ...
        last_name, email_address, user_id, token, profile_id, login_level, ...
        remember_me, email_address, display_name);
    % Clear all local variables from users workspace.
    clear li login_level user_id first_name last_name email_address profile_id display_name token remember_me
end

if (strlength(getenv('MWI_BASE_URL')) > 0)
    connector.internal.setConfig('contextRoot', getenv('MWI_BASE_URL'))
end
connector.internal.Worker.start

% Add-on explorer is not supported in this environment.
% The following settings instructs it to display appropriate error messages when used.
matlab_settings = settings;
matlab_settings.matlab.addons.explorer.addSetting('isExplorerSupported');
matlab_settings.matlab.addons.explorer.isExplorerSupported.PersonalValue = false;

clear matlab_settings