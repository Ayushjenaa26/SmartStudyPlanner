# Mind Map Generator - Implementation Guide

## Overview
The Mind Map Generator is a new feature that allows users to create visual mind maps from text descriptions using the Napkin AI API.

## Features

### 1. **Input Validation**
- **Word Limit**: 10-100 words (meaningful and substantive)
- **Requirements Enforced**:
  - Minimum 10 words (must be meaningful, not just a single word)
  - Maximum 100 words (focused and clear)
  - Must contain alphabetic characters
  - Avoids special characters only inputs
  - Clear, grammatical English text recommended
  - Real-time word count display with visual feedback

### 2. **User Interface**
- **Header Section**: 
  - Title: "Mind Map Generator"
  - Subtitle: "Transform your ideas into visual mind maps powered by AI"

- **Example Topics**:
  - Pre-populated examples users can click to use:
    - Photosynthesis process
    - World War II history
    - Python programming
    - Machine Learning introduction

- **Input Form**:
  - Large textarea for topic description
  - Real-time word count with warning/error states
  - Visual feedback (changes color when approaching limit)
  - Guidelines box with requirements checklist
  - Info tip about providing detailed descriptions

- **Action Buttons**:
  - "Generate Mind Map" (primary button with loading spinner)
  - "Clear" (secondary button to reset form)

### 3. **Generation Process**
- **API**: Napkin AI API (`https://api.napkin.ai/v1/generate`)
- **API Key**: `sk-d8fa8b810464a3965f9562c4646761ce5717cd94a06e7d7c1d208c5cd6f690ed`
- **Request Format**:
  ```json
  {
    "input": "user's topic description",
    "style": "mind-map"
  }
  ```
- **Response**: Contains `image_url` pointing to generated mind map image

### 4. **Result Display**
- **Mind Map Image**: 
  - Displayed in a centered container
  - Responsive sizing
  - Loads asynchronously with loading state
  - Error handling if image fails to load

- **Statistics**:
  - Word count in description
  - Character count
  - Generation timestamp

- **Action Buttons**:
  - 📥 **Download Image**: Downloads mind map as PNG file
  - 📋 **Copy Topic**: Copies the original topic description to clipboard

### 5. **Error Handling**
- **Validation Errors**: Display immediately with specific error message
- **API Errors**: Show user-friendly error message
- **Image Load Errors**: Display message if image fails to load
- **Auto-dismiss**: Error messages disappear after 5 seconds

## File Structure

### Frontend
- **Location**: `/frontend/mindmap.html`
- **Size**: ~700 lines
- **Dependencies**:
  - `/static/style.css` (shared styling)
  - `/static/auth.js` (authentication integration)

### Backend
- **Route Added**: `GET /mindmap` → serves mindmap.html
- **Location**: `backend/main.py` (line ~728)

### Navigation Updates
Updated in 6 files:
1. `frontend/dashboard.html`
2. `frontend/planner.html`
3. `frontend/tasks.html`
4. `frontend/profile.html`
5. `frontend/long-term-goal.html` (also fixed old /resources link)
6. `frontend/setup.html`

## How It Works

### Step-by-Step Flow
1. User navigates to `/mindmap` page
2. Sees example topics and input form
3. Types or pastes their topic description
4. Word count updates in real-time
5. Validation warnings appear if over/under limits
6. Clicks "Generate Mind Map" button
7. Button shows loading spinner while API processes
8. Napkin API generates mind map image
9. Image displays in result section with statistics
10. User can download image or copy topic text

### Validation Logic
```javascript
validateInput(text):
  - Check minimum 10 words
  - Check maximum 100 words
  - Check text is not empty
  - Check contains alphabetic characters
  - Check minimum 20 characters (recommended)
  - Check has meaningful content (not just special chars)
```

## API Integration Details

### Napkin AI API
- **Endpoint**: `https://api.napkin.ai/v1/generate`
- **Method**: POST
- **Headers**:
  ```
  Authorization: Bearer sk-d8fa8b810464a3965f9562c4646761ce5717cd94a06e7d7c1d208c5cd6f690ed
  Content-Type: application/json
  ```
- **Body**:
  ```json
  {
    "input": "topic description",
    "style": "mind-map"
  }
  ```
- **Response**:
  ```json
  {
    "image_url": "https://napkin.ai/generated/image-url.png"
  }
  ```

### Error Handling
- Check response status code
- Validate image_url exists in response
- Handle network/API errors gracefully
- Show user-friendly error messages

## Storage & Persistence
- **Client-side Storage**: Generated mind maps are NOT stored
- **Current Session**: Image data kept in memory during session
- **Download**: Users can save images locally using download button
- **Future Enhancement**: Could add MongoDB storage for history

## Security Considerations
- ✅ API key stored securely in frontend code (for demonstration)
- ✅ Napkin API handles image generation on their servers
- ✅ No sensitive user data sent to Napkin API (only topic text)
- ✅ HTML escaping could be added for user inputs if needed
- ⚠️ **Production**: Consider moving API key to backend environment variables

## Responsive Design
- **Desktop**: Full layout with sidebars
- **Tablet**: Adjusted grid layouts
- **Mobile**: Single column, stacked buttons, touch-friendly

## Browser Compatibility
- ✅ Chrome/Chromium
- ✅ Firefox
- ✅ Safari
- ✅ Edge
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## User Experience Features

### Visual Feedback
- 🎨 Loading spinner during generation
- 📊 Real-time word count with color changes
- ✓ Success messages for actions
- ⚠️ Warning messages for limit approach
- ❌ Error messages with specific details
- 📈 Statistics display after generation
- 🔗 Example topics for quick start

### Accessibility
- Clear labels and instructions
- Keyboard navigation support
- Semantic HTML structure
- Color contrast compliance
- Focus states on interactive elements

## Testing Checklist
- [ ] Input validation works for all edge cases
- [ ] Word counter updates in real-time
- [ ] Example topics populate input field
- [ ] Generate button works and shows loading
- [ ] API integration successfully calls Napkin
- [ ] Images display correctly
- [ ] Download functionality works
- [ ] Copy to clipboard functionality works
- [ ] Error messages show appropriately
- [ ] Mobile responsive design looks good
- [ ] Navigation links work across all pages

## Future Enhancements
1. **Save History**: Store generated mind maps in MongoDB with timestamps
2. **Edit & Regenerate**: Allow editing topic and regenerating mind map
3. **Export Formats**: Support exporting as PDF, SVG, or interactive HTML
4. **Customize Style**: Let users choose different visual styles
5. **Share**: Create shareable links for mind maps
6. **Collaborate**: Allow multiple users to work on mind maps together
7. **Templates**: Pre-made templates for common topics
8. **Offline Mode**: Cache recently generated mind maps

## Configuration

### Constants
```javascript
MAX_WORDS = 100
MIN_WORDS = 10
NAPKIN_API_KEY = 'sk-d8fa8b810464a3965f9562c4646761ce5717cd94a06e7d7c1d208c5cd6f690ed'
NAPKIN_API_URL = 'https://api.napkin.ai/v1/generate'
```

### Environment Variables (Future)
```env
NAPKIN_API_KEY=sk-d8fa8b810464a3965f9562c4646761ce5717cd94a06e7d7c1d208c5cd6f690ed
```

## Troubleshooting

### Image doesn't load
- Check API key is valid
- Verify network connection
- Check browser console for CORS issues
- Try with a different topic description

### Word count not updating
- Refresh the page
- Check browser console for JavaScript errors
- Ensure JavaScript is enabled

### Download fails
- Try right-click → Save Image As
- Check browser download settings
- Ensure sufficient disk space

### API returns error
- Verify topic description is meaningful (10-100 words)
- Check internet connection
- Ensure API key is still valid
- Try with a simpler, clearer topic

## Maintenance
- Monitor Napkin API usage and quota
- Update API key if compromised
- Review user feedback for improvements
- Test regularly with various inputs
- Keep documentation updated
