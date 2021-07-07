# Development Customization

To develop the JavaScript Single-page application and Python application with live-reloading,
start a development server for both.
The JavaScript development server proxies all requests that it does not recognise
to the Python development server.

To start the JavaScript development server, execute:

```bash
# Change into the directory gui
cd gui
# Install the node dependencies
npm install
# Start the development server
npm start
```

To start the Python development server, in a separate shell, execute:

```bash
# Create a Python virtual environment if one does not already exist (skip this step if one exists)
python -m venv .venv
# Activate the Python virtual environment (skip this if already done)
source .venv/bin/activate
# Install the Python package (and dependencies) in development mode (skip this if already done)
pip install -e .[dev]
# Start the development server
MWI_DEV=true adev runserver jupyter_matlab_proxy/app.py
```

If you make any changes to either the JavaScript code or the Python code, then these apps will reload immediately showing the results. Bear in mind that this kind of live-reloading can have an impact on application state (on the serverside particularly). This occurs independently for the JavaScript and Python applications. So if you are working only on the frontend, the backend state will never be affected by changes to the frontend and vice-versa.

In development mode, no MATLAB is required. Where MATLAB and Xvfb would have their processes launched, placeholder processes are launched in their stead.
