# 🧪 Groq Migration Testing Guide

## Quick Start

### 1. Install Dependencies
```bash
cd elysium_streamlit_app
pip install groq>=0.4.0
```

### 2. Configure API Key (REQUIRED)
**⚠️ IMPORTANT: Follow the security setup guide first!**

See `SECURITY_SETUP.md` for detailed instructions.

**Quick setup:**
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your Groq API key
# GROQ_API_KEY="gsk_your_key_here"
```

### 3. Verify Environment
```bash
# Check API key is set (without revealing it)
python -c "import os; print('✅ Key configured' if os.getenv('GROQ_API_KEY') else '❌ Key missing')"
```

### 4. Launch Application
```bash
streamlit run app.py
```

## Test Scenarios

### Test 1: Catalogue AI Search
**Location**: Main Catalogue tab

**Steps**:
1. Navigate to the Catalogue tab (first tab)
2. Find the "🤖 Natural Language Search" input field
3. Enter: `"taller blonde models with blue eyes from development"`
4. Click "🔍 AI Search" button
5. Wait for processing (should take 2-3 seconds)

**Expected Results**:
- ✅ No error messages appear
- ✅ Filters are automatically populated:
  - Hair color: blonde
  - Eye color: blue
  - Height: relative (taller)
  - Division: dev
- ✅ Model results update to match the filters
- ✅ Results show models matching the criteria

**Troubleshooting**:
- If error "Groq client not initialized": Check API key in `.env`
- If timeout: Check internet connectivity
- If no results: Try a broader query

---

### Test 2: Athena Client Brief Parsing
**Location**: Athena tab (🏛️ Athena)

**Steps**:
1. Navigate to the Athena tab (second tab)
2. Find the "Client Brief" text area
3. Enter: `"Looking for a blonde, blue-eyed model size 0-4 for a cowboy boots campaign in the desert"`
4. Click "🎯 Generate Pitchback" button
5. Wait for processing

**Expected Results**:
- ✅ Status shows "🧠 Parsing client brief..."
- ✅ Parsed filters appear in the interface:
  - Hair: blonde
  - Eyes: blue
  - Size: 0-4
  - Campaign: cowboy boots
  - Location: desert
- ✅ Matching models are displayed
- ✅ Progress bar completes

**Troubleshooting**:
- If "Failed to connect to AI service": Check API key
- If no filters extracted: Try a more specific brief
- If no models found: Adjust the brief criteria

---

### Test 3: Athena Email Generation
**Location**: Athena tab (🏛️ Athena)

**Prerequisites**: Complete Test 2 first to have models selected

**Steps**:
1. After models are matched (from Test 2)
2. Select 2-3 models from the results
3. The email should auto-generate
4. Review the generated email in the right panel

**Expected Results**:
- ✅ Professional email is generated
- ✅ Email includes:
  - Subject line
  - Professional greeting
  - Model details (names, attributes)
  - Campaign context
  - Professional closing with "Elysium Agency"
- ✅ Email is well-formatted and coherent
- ✅ Copy button works (if pyperclip installed)

**Troubleshooting**:
- If email is empty: Check console for errors
- If email is garbled: May need to regenerate
- If copy fails: Install pyperclip (`pip install pyperclip`)

---

## Advanced Testing

### Test 4: Rate Limiting
**Purpose**: Verify rate limiting works correctly

**Steps**:
1. Make 5 rapid AI search queries in succession
2. Observe timing between responses

**Expected Results**:
- ✅ Each request completes successfully
- ✅ Minimum 40ms delay between API calls
- ✅ No rate limit errors from Groq

---

### Test 5: Error Handling
**Purpose**: Verify graceful error handling

**Test 5a: Invalid API Key**
1. Temporarily modify `.env` to have invalid key
2. Try any AI feature
3. **Expected**: Clear error message about API key

**Test 5b: Network Disconnected**
1. Disconnect internet
2. Try any AI feature
3. **Expected**: Timeout error with helpful message

**Test 5c: Empty Input**
1. Submit empty query to AI search
2. **Expected**: No API call made, validation message

---

## Performance Benchmarks

### Expected Response Times
- **Catalogue AI Search**: 1-3 seconds
- **Athena Brief Parsing**: 2-4 seconds
- **Email Generation**: 3-5 seconds

### API Usage Monitoring
Monitor your Groq API usage at: https://console.groq.com

**Free Tier Limits**:
- 30 requests per minute
- 14,400 requests per day
- 500,000 tokens per day

---

## Common Issues & Solutions

### Issue: "Groq client not initialized"
**Solution**:
- Check `.env` file exists in `elysium_streamlit_app/`
- Verify API key format: `GROQ_API_KEY="gsk_..."`
- Ensure variable name is `GROQ_API_KEY` (not `groq`)
- Restart Streamlit app
- See `SECURITY_SETUP.md` for detailed troubleshooting

### Issue: "Failed to get response from Groq API"
**Solution**:
- Check internet connectivity
- Verify API key is valid
- Check Groq service status

### Issue: "Could not parse AI response as JSON"
**Solution**:
- This is usually temporary
- Try the query again
- If persistent, the prompt may need adjustment

### Issue: Slow responses
**Solution**:
- Normal for first request (cold start)
- Subsequent requests should be faster
- Check internet speed

---

## Success Criteria Checklist

After testing, verify:

- [ ] ✅ Catalogue AI search works without errors
- [ ] ✅ Athena brief parsing extracts correct filters
- [ ] ✅ Athena email generation creates professional emails
- [ ] ✅ No Ollama-related errors appear
- [ ] ✅ Response times are acceptable (< 5 seconds)
- [ ] ✅ Error messages are clear and helpful
- [ ] ✅ Rate limiting prevents API overuse
- [ ] ✅ All features work consistently

---

## Reporting Issues

If you encounter issues:

1. **Check the console** for error messages
2. **Note the exact steps** to reproduce
3. **Capture error messages** (screenshots helpful)
4. **Check API usage** on Groq console
5. **Review logs** in terminal running Streamlit

---

## Next Steps After Testing

Once all tests pass:

1. ✅ Mark migration as complete
2. 📝 Update user documentation
3. 🚀 Deploy to production
4. 📊 Monitor API usage and costs
5. 🔄 Consider implementing response caching for common queries

---

## Quick Test Commands

```bash
# Install dependencies
pip install groq>=0.4.0

# Verify installation
python -c "from groq import Groq; print('Groq installed successfully')"

# Check environment (secure - doesn't print the key)
python -c "import os; print('API Key:', 'Found' if os.getenv('GROQ_API_KEY') else 'Missing')"

# Test Groq client initialization
python -c "from groq_client import GroqClient; c = GroqClient(); print('✅ Client initialized')"

# Run app
streamlit run app.py
```

---

## Support

For issues or questions:
- Review `GROQ_MIGRATION_SUMMARY.md` for technical details
- Check Groq documentation: https://console.groq.com/docs
- Review error logs in Streamlit console

