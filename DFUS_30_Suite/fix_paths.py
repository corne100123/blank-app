import os

# 1. The folder where your tools are located
tools_folder = "../tools"

# 2. The code currently in your files (the broken relative path)
# We look for both single and double quotes just in case
bad_code_1 = 'sqlite3.connect(r"D:\\DFUS_30_Suite\\NewLoanManager.db")'
bad_code_2 = "sqlite3.connect(r'D:\\DFUS_30_Suite\\NewLoanManager.db')"

# 3. The fix: The absolute path to the database
# For Linux
new_code = 'sqlite3.connect("../NewLoanManager.db")'

print("--- Starting Auto-Fixer ---")

# Loop through every file in the tools folder
for filename in os.listdir(tools_folder):
    if filename.endswith(".py"):
        file_path = os.path.join(tools_folder, filename)
        
        # Read the file
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check if it needs fixing
        if bad_code_1 in content or bad_code_2 in content:
            # Replace the bad path with the new absolute path
            new_content = content.replace(bad_code_1, new_code)
            new_content = new_content.replace(bad_code_2, new_code)
            
            # Save the file back
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            print(f"✅ Fixed: {filename}")
        else:
            print(f"Skipped: {filename} (Already correct or not using DB)")

print("--- Done! Try running the app now. ---")