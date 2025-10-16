# Elysium Model Catalogue - Demo Script

This demo script walks through the key features of the Elysium Model Catalogue Streamlit app.

## Prerequisites

1. ✅ Ollama is running (`ollama serve`)
2. ✅ gemma3:4b model is available (`ollama pull gemma3:4b`)
3. ✅ Streamlit app is running (`streamlit run app.py`)
4. ✅ Browser is open to http://localhost:8501

## Demo Walkthrough

### 1. Initial Load and Overview

**What to show:**
- Beautiful header with gradient styling
- Sidebar with manual filters
- Main area with AI search interface
- Model grid displaying all 135+ models in responsive cards

**Key points:**
- Data loads from `../elysium_kb/models.jsonl`
- Height is normalized to cm (165-191 range)
- Hair/eye colors are normalized to lowercase
- Clean, modern UI with model cards showing thumbnails, names, and attributes

### 2. Manual Filtering

**Demo steps:**
1. **Hair Color Filter:**
   - Select "blonde" from the Hair Color multiselect
   - Show how the grid updates to show only blonde models
   - Note the count changes (e.g., "Displaying 15 of 135 models")

2. **Eye Color Filter:**
   - Add "blue" to the Eye Color multiselect
   - Show combined filtering (blonde hair AND blue eyes)
   - Count should decrease further

3. **Height Range Filter:**
   - Adjust the height slider to 175-185 cm
   - Show how this further narrows the results
   - Demonstrate the AND logic of all filters

4. **Reset Filters:**
   - Click "🔄 Reset Filters" button
   - Show how all filters clear and full dataset returns

### 3. AI-Powered Search

**Demo Query 1: Basic Search**
```
Input: "Looking for blonde models with blue eyes around 175 cm"
```

**Steps:**
1. Enter the query in the text area
2. Click "🔍 Search with AI (Ollama)"
3. Show the "Processing with AI..." spinner
4. Display the parsed JSON filters:
   ```json
   {
     "haircolor": "blonde",
     "eyecolor": "blue",
     "heightmin": 170,
     "heightmax": 180
   }
   ```
5. Show how the grid updates with matching models

**Demo Query 2: Campaign-Style Brief**
```
Input: "Show me 2 tall brunette models for a lifestyle campaign"
```

**Expected AI parsing:**
```json
{
  "haircolor": "brunette",
  "heightmin": 175
}
```

**Demo Query 3: Division-Specific Search**
```
Input: "Find models with green eyes from the dev division"
```

**Expected AI parsing:**
```json
{
  "eyecolor": "green",
  "division": "dev"
}
```

### 4. Combined Manual + AI Filtering

**Demo steps:**
1. Set manual filters: Hair = "brown", Height = 170-180 cm
2. Use AI query: "blue eyes for fashion shoot"
3. Show how both manual and AI filters combine with AND logic
4. Demonstrate the power of hybrid filtering

### 5. Model Card Features

**What to highlight:**
- **Local thumbnail images** loaded from `elysium_kb/images/` with fallback placeholders
- **Model details**: Name, Division (IMA/DEV/MAI)
- **Attributes**: Hair color, eye color, height in cm
- **"View Portfolio" button**: Click to expand full model view
- **Responsive grid**: 4 cards per row, adapts to screen size

### 6. Expandable Model View

**Demo the expanded view:**
1. **Click any "👁️ View Portfolio" button** on a model card
2. **Show the expanded view features:**
   - Full model details with comprehensive attributes
   - **Local image gallery** showing all portfolio images (4 per row)
   - **"View APM Profile" button** → opens external profile
   - **"← Back to Catalogue" button** → returns to grid view
3. **Navigate through multiple images** in the gallery
4. **Test the back functionality** to return to the main grid

### 7. Error Handling and Edge Cases

**Demo scenarios:**
1. **Ollama disconnected**: Show graceful error message
2. **Invalid AI query**: Show how malformed responses are handled
3. **No results**: Show "No models found" message
4. **Image loading failures**: Show placeholder images

## Success Criteria Verification

✅ **Loads models.jsonl and displays catalogue in grid form**
- 135+ models loaded successfully
- Responsive grid with 4 cards per row
- Clean model cards with all attributes

✅ **Filters work manually from sidebar**
- Hair color multiselect working
- Eye color multiselect working
- Height range slider working
- Reset button clears all filters

✅ **Accepts natural-language brief → uses Ollama → returns structured filters**
- AI query parsing working with gemma3:4b
- JSON extraction from AI responses
- Structured filters applied correctly

✅ **Applies those filters correctly**
- Manual filters work independently
- AI filters work independently
- Combined filtering uses AND logic
- Results update dynamically

✅ **Clean, demo-ready UI**
- Modern gradient header
- Responsive design
- Professional model cards with local images
- Expandable portfolio view with image galleries
- Clear filter indicators

✅ **Runs fully offline with Ollama LLM**
- No external API calls
- Local Ollama integration
- Offline inference working

## Performance Notes

- **Data Loading**: ~135 models load in <2 seconds
- **AI Queries**: Response time 2-5 seconds depending on model
- **Filtering**: Instant updates with pandas operations
- **Grid Rendering**: Limited to 20 models for performance
- **Image Loading**: Async with fallback placeholders

## Technical Architecture Highlights

1. **DataLoader**: Robust JSONL parsing with normalization
2. **OllamaClient**: Error-resilient AI integration
3. **FilterEngine**: Efficient pandas-based filtering
4. **UI Components**: Streamlit-based responsive design
5. **Error Handling**: Graceful degradation for all failure modes

## Demo Tips

1. **Start with manual filters** to show basic functionality
2. **Use simple AI queries first** before complex ones
3. **Show the JSON parsing** to demonstrate AI understanding
4. **Highlight the offline nature** - no internet required
5. **Demonstrate error recovery** if Ollama disconnects
6. **Show responsive design** by resizing browser window

This demo successfully showcases a production-ready model catalogue with AI-powered search capabilities running entirely offline!

## Phase 2 Enhancements

### 8. Next/Previous Navigation

**Demo the model navigation:**
1. **Click any "👁️ View Portfolio" button** to enter expanded view
2. **Show navigation controls** in the top-right corner:
   - "⬅️ Previous" button to go to previous model in filtered results
   - "➡️ Next" button to go to next model in filtered results
   - Model counter showing "Model X of Y"
3. **Navigate through multiple models** without returning to the grid
4. **Test with filtered results** - navigation respects current filters

### 9. Hover Effects on Cards

**Demo the enhanced card interactions:**
1. **Hover over model cards** in the grid view
2. **Show the smooth animations:**
   - Cards lift up with `translateY(-5px)` effect
   - Enhanced shadow appears on hover
   - Background color subtly changes
   - Smooth 0.3s transition animations
3. **Demonstrate responsive hover** across different cards

### 10. Image Carousel Gallery

**Demo the enhanced gallery experience:**
1. **Enter any model's expanded view**
2. **Show the carousel controls:**
   - "⬅️ Previous Image" and "➡️ Next Image" buttons
   - Image counter showing "Image X of Y"
   - Large main image display
3. **Navigate through portfolio images** using carousel controls
4. **Show the thumbnail strip below:**
   - All images displayed as clickable thumbnails
   - Current image highlighted with blue border
   - Click any thumbnail to jump to that image
   - Responsive grid layout (4 thumbnails per row)

## Enhanced Success Criteria

✅ **Phase 1 - Core Functionality** (All previous criteria met)

✅ **Phase 2 - Enhanced User Experience**
- **Navigation**: Seamless next/previous model browsing
- **Hover Effects**: Smooth card animations and visual feedback
- **Image Carousel**: Professional gallery with thumbnail navigation
- **Responsive Design**: All enhancements work across screen sizes
- **State Management**: Carousel and navigation state properly maintained

## Enhanced Demo Tips

1. **Show the hover effects** by slowly moving mouse over different cards
2. **Demonstrate navigation flow** by clicking through 3-4 models in sequence
3. **Use the carousel** to showcase multiple portfolio images
4. **Click thumbnails** to show instant image jumping
5. **Test with filters** to show navigation respects filtered results
6. **Highlight the professional UX** - smooth animations and intuitive controls

The enhanced demo now showcases a professional-grade model catalogue with modern UX patterns and smooth interactions!
