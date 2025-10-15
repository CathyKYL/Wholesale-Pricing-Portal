# 🔧 Setup Supabase PATH Environment Variable

## 📍 Your Supabase Location
```
C:\VibeCode\Wholesale Pricing Portal\Supabase
```

---

## 🚀 Quick Setup (Automatic)

### Option 1: Use the Batch File (Easiest)

1. **Run as Administrator:**
   - Right-click `add-supabase-to-path.bat`
   - Select "**Run as administrator**"
   - Approve the UAC prompt
   - Wait for confirmation

2. **Close and reopen** your terminal/PowerShell

3. **Test it works:**
   ```bash
   supabase --version
   ```

---

## 🔧 Manual Setup (Alternative)

### Step 1: Open Environment Variables

1. Press `Windows Key` + `R`
2. Type: `sysdm.cpl`
3. Press Enter
4. Click "**Advanced**" tab
5. Click "**Environment Variables**" button

### Step 2: Edit PATH Variable

1. Under "**System variables**" (bottom section)
2. Find and select "**Path**"
3. Click "**Edit...**"
4. Click "**New**"
5. Add this path:
   ```
   C:\VibeCode\Wholesale Pricing Portal\Supabase
   ```
6. Click "**OK**" on all dialogs

### Step 3: Verify Installation

1. **Close all** PowerShell/Command Prompt windows
2. **Open a new** PowerShell window
3. **Test the command:**
   ```bash
   supabase --version
   ```

You should see something like:
```
1.xxx.xxx
```

---

## 🔍 Alternative: Add to Current Session Only (Temporary)

If you don't want to modify system PATH permanently, you can add it just for your current PowerShell session:

```powershell
$env:Path += ";C:\VibeCode\Wholesale Pricing Portal\Supabase"
```

Then verify:
```bash
supabase --version
```

**Note:** This will only work in the current PowerShell window. When you close it, you'll need to run the command again.

---

## 🎯 After PATH is Set

Once Supabase is in your PATH, you can run these commands from anywhere:

### 1. Login to Supabase
```bash
supabase login
```

### 2. Link Your Project
```bash
supabase link --project-ref mofhylcyainzwbrcmrqg
```

### 3. Deploy Edge Function
```bash
supabase functions deploy generate_quote
```

### 4. Set Secrets
```bash
supabase secrets set SUPABASE_URL=https://mofhylcyainzwbrcmrqg.supabase.co
supabase secrets set SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1vZmh5bGN5YWluendicmNtcnFnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjAzNDg1MTQsImV4cCI6MjA3NTkyNDUxNH0.TeaalZbVrSkqAszpZxPDSJUdoXL0wsg9veDhS1v8Bj0
```

---

## 🐛 Troubleshooting

### Issue: "supabase is not recognized"

**Causes:**
1. PATH not set correctly
2. Terminal not restarted after setting PATH
3. Wrong directory path

**Solutions:**

1. **Verify the directory exists:**
   ```bash
   dir "C:\VibeCode\Wholesale Pricing Portal\Supabase"
   ```
   
2. **Check if supabase.exe is in the folder:**
   ```bash
   dir "C:\VibeCode\Wholesale Pricing Portal\Supabase\supabase.exe"
   ```

3. **Verify PATH was added:**
   ```powershell
   $env:Path -split ';' | Select-String -Pattern 'Supabase'
   ```

4. **Close and reopen terminal** (important!)

5. **Test again:**
   ```bash
   supabase --version
   ```

### Issue: "Access Denied" when running batch file

**Solution:** Run the batch file as Administrator
- Right-click → "Run as administrator"

### Issue: Still not working after all steps

**Alternative - Use full path:**
```bash
& "C:\VibeCode\Wholesale Pricing Portal\Supabase\supabase.exe" --version
& "C:\VibeCode\Wholesale Pricing Portal\Supabase\supabase.exe" login
& "C:\VibeCode\Wholesale Pricing Portal\Supabase\supabase.exe" functions deploy generate_quote
```

Or create an alias in your PowerShell profile:
```powershell
notepad $PROFILE
```

Add this line:
```powershell
Set-Alias supabase "C:\VibeCode\Wholesale Pricing Portal\Supabase\supabase.exe"
```

---

## ✅ Success Checklist

After setup, verify these work:

- [ ] `supabase --version` shows version number
- [ ] `supabase login` opens browser for login
- [ ] `supabase link --project-ref mofhylcyainzwbrcmrqg` links project
- [ ] Can run `supabase` commands from any directory

---

## 🎊 Next Steps After PATH is Set

1. ✅ **Login:**
   ```bash
   supabase login
   ```

2. ✅ **Link project:**
   ```bash
   supabase link --project-ref mofhylcyainzwbrcmrqg
   ```

3. ✅ **Deploy Edge Function:**
   ```bash
   supabase functions deploy generate_quote
   ```

4. ✅ **Test your website!**
   - Open `Front end/index.html`
   - Search for a product
   - Click on it
   - Watch the quote calculate! 🎉

---

**Your Supabase CLI will be ready to use from anywhere!** 🚀





