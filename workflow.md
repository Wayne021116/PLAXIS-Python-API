# Getting Started

## 1. Install plxscripting

PLAXIS 2D ships with its own Python interpreter and the `plxscripting` module. To use your own Python environment (e.g. Anaconda), you need to manually copy the module files.

**Step 1** — Open the PLAXIS built-in Python interpreter and run the following to find the module path:
```python
import plxscripting
print(plxscripting.__file__)
```

This will return a path similar to:
```
C:\ProgramData\Bentley\Geotechnical\PLAXIS Python Distribution V2\python\lib\site-packages\plxscripting\__init__.py
```

**Step 2** — Navigate to the `site-packages` folder shown above. Copy the following three items:
- `plxscripting` folder
- `Crypto` folder
- `encryption.py` file

**Step 3** — Paste the copied items into your own Python environment's `site-packages` folder. For Anaconda, this is typically located at:
```
C:\Users\<YourName>\anaconda3\Lib\site-packages\
```

Once complete, your Python interpreter can communicate with PLAXIS 2D via the remote scripting API.

---

## 2. Enable Remote Scripting in PLAXIS 2D

Before running any script, you must enable the remote scripting server inside PLAXIS 2D:

1. Open **PLAXIS 2D**
2. Go to **Expert (X) → Configure Remote Scripting Server**
3. Check **Enable remote scripting server**
4. Set the **port** to `10000` (default)
5. Set a **password** of your choice (minimum 4 characters)
6. Click **OK**

> If port `10000` is already in use on your machine, change it to `9999` or any available port. Make sure to update the port number in the scripts accordingly.

---

## 3. Configure the Scripts

Before running any script, make two changes:

**Change 1 — Set your password:**

Find the following line at the top of each script and replace `"your password"` with the password you set in PLAXIS:
```python
passwd = "your password"
```

**Change 2 — Set your save path:**

Find the `save_path` line in each script and update the path to a folder that exists on your machine:
```python
# Example — change this to your own path
save_path = r"D:\PLAXIS\your_project_name.p2dx"
```

Also update the Output server open path to match:
```python
s_o.open(r"D:\PLAXIS\your_project_name.p2dx")
```

**Change 3 — If using a different port:**

If you changed the port from `10000` to `9999`, update the connection line:
```python
# Change 10000 to your actual port number
s_i, g_i = new_server("localhost", 9999, password=passwd,
                       timeout=3600, request_timeout=3600)
```

---

## 4. Run a Script

Once PLAXIS 2D is open and the remote scripting server is enabled, run any script from your terminal or IDE:
```bash
python slope_analysis.py
```

The script will automatically connect to PLAXIS, build the model, run the calculation, and print the results.
