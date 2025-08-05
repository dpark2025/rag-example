# RAG System Quick Start Tutorial

**Authored by: Harry Lewis (louie) - Technical Writer**  
**Date: 2025-08-04**

Get up and running with your local RAG system in under 10 minutes! This tutorial will walk you through your first successful document upload and question.

## 🎯 Tutorial Goals

By the end of this tutorial, you will:
- ✅ Have your RAG system running locally
- ✅ Upload your first document successfully  
- ✅ Ask your first question and get an answer with sources
- ✅ Understand the basic interface and navigation

**Estimated Time:** 5-10 minutes

---

## 🚀 Quick Setup

### Prerequisites Check

Before starting, ensure you have:
- [ ] **Ollama installed and running** (`ollama serve`)
- [ ] **A language model downloaded** (e.g., `ollama pull llama3.2:3b`)
- [ ] **Python 3.11+** with pip installed
- [ ] **Docker or Podman** installed (for containerized setup)

### Option 1: Instant Start (Recommended)

**If your system is already set up:**

1. **Start the system:**
   ```bash
   # Open terminal and run:
   make setup
   
   # In a new terminal:
   cd app/reflex_app && reflex run
   ```

2. **Open your browser:** Go to http://localhost:3000

3. **Ready!** Skip to [Your First Document](#your-first-document) below.

### Option 2: First-Time Setup

**If this is your first time:**

1. **Install dependencies:**
   ```bash
   pip install -r requirements.reflex.txt
   pip install -r app/requirements.txt
   ```

2. **Start Ollama:**
   ```bash
   ollama serve
   # Keep this terminal open
   ```

3. **Start RAG backend (new terminal):**
   ```bash
   cd app && python main.py
   ```

4. **Start Reflex UI (new terminal):**
   ```bash
   cd app/reflex_app && reflex run
   ```

5. **Open browser:** Go to http://localhost:3000

---

## 📄 Your First Document

### Step 1: Access Document Management

1. **Open the interface** at http://localhost:3000
2. **Check the system status** in the left sidebar:
   - Look for green indicators (🟢) showing "System Online"
   - If you see red indicators, check that all services are running
3. **Click "Documents"** in the left sidebar

### Step 2: Upload a Test Document

**Choose a document to upload:**
- A PDF file (report, article, manual)
- A text file (.txt, .md)
- Any document you'd like to ask questions about

**Upload process:**
1. **Click "Upload Documents"** button or drag-and-drop area
2. **Select your file** from your computer
3. **Watch the progress bar** as your document uploads
4. **Wait for processing** - you'll see status change from "Processing" to "Complete"

> **💡 Tip:** Start with a smaller document (under 10MB) for your first try.

### Step 3: Verify Upload Success

**Check your document appears in the library:**
- Document name is displayed correctly
- Status shows ✅ "Complete" 
- File size and type are shown
- Upload timestamp is recent

**If upload failed:**
- Check file isn't password-protected
- Ensure file contains readable text (not just images)
- Try a smaller file if the original was very large

---

## 💬 Your First Question

### Step 1: Navigate to Chat

1. **Click "Chat"** in the left sidebar
2. **You should see:**
   - Welcome message in the chat area
   - Input box at the bottom
   - Settings panel on the right (similarity threshold, max chunks)
   - System status indicators

### Step 2: Ask a Simple Question

**Start with a straightforward question about your document:**

**Good first questions:**
- "What is this document about?"
- "Summarize the main points"
- "What are the key topics covered?"
- "What is the document's purpose?"

**Type your question and click Send or press Enter.**

### Step 3: Understand the Response

**Watch for the response process:**
1. **Typing indicator** appears while processing
2. **Answer streams in** word by word
3. **Source badges** appear showing which document was referenced
4. **Response metrics** show processing time

**Response elements:**
- **Main answer** in the chat bubble
- **Source citation** as clickable badges (e.g., "📄 your-document.pdf")
- **Processing time** and performance info

### Step 4: Try a Follow-up Question

**Ask a more specific question based on the first response:**
- "Tell me more about [specific topic mentioned]"
- "What details are provided about [something from the first answer]?"
- "How does the document explain [specific concept]?"

---

## 🎛️ Basic Settings and Features

### Chat Settings

**In the right panel, you can adjust:**

**Similarity Threshold (0.0-1.0):**
- **0.7-1.0:** Very relevant content only (precise answers)
- **0.5-0.7:** Balanced relevance (recommended for beginners)
- **0.3-0.5:** Broader content inclusion (comprehensive answers)

**Max Chunks (1-10):**
- **2-3:** Faster responses, focused answers
- **4-5:** Good balance (recommended for beginners)
- **6-10:** More comprehensive but slower

> **💡 Recommendation:** Keep default settings (0.7 similarity, 3 max chunks) for your first questions.

### Navigation Features

**Left Sidebar:**
- **Chat:** Ask questions and view conversation history
- **Documents:** Manage your document library
- **System Status:** Health indicators for all components

**Chat Interface:**
- **Scroll up** to see previous conversations
- **Clear chat** button to start fresh
- **Source badges** are clickable for more context

---

## ✅ Success Checklist

After completing this tutorial, you should be able to:

- [ ] **Upload documents** successfully and see them in your library
- [ ] **Ask questions** and get responses with source citations  
- [ ] **Navigate** between Chat and Documents sections
- [ ] **Adjust basic settings** like similarity threshold and max chunks
- [ ] **Monitor system health** through the status indicators
- [ ] **Use source citations** to understand where answers come from

---

## 🎉 What's Next?

### Immediate Next Steps

1. **Upload more documents** to build your knowledge base
2. **Try different question types** (summaries, comparisons, specific facts)
3. **Experiment with settings** to see how they affect responses
4. **Explore document management** features (search, filter, organize)

### Explore Advanced Features

- **Bulk document upload** for large collections
- **Document search and filtering** for better organization  
- **Advanced question techniques** for complex analysis
- **System monitoring** for performance optimization

### Learn More

- **[User Manual](user_manual.md)** - Comprehensive guide to all features
- **[Feature Overview](feature_overview.md)** - Detailed capability descriptions
- **[Troubleshooting FAQ](troubleshooting_faq.md)** - Solutions to common issues

---

## 🛟 Quick Troubleshooting

### Common First-Time Issues

**❌ "Cannot connect to RAG backend"**
```bash
# Check if backend is running:
curl http://localhost:8000/health

# If not running, start it:
cd app && python main.py
```

**❌ "System Offline" indicators**
```bash
# Check Ollama is running:
curl http://localhost:11434/api/tags

# If not running:
ollama serve
```

**❌ Document upload fails**
- Check file size (recommend <50MB for first uploads)
- Ensure file isn't password-protected
- Try a different file format (PDF or TXT work best)

**❌ No response to questions**
- Verify at least one document shows "Complete" status
- Try asking a simpler, more direct question
- Check system health indicators are green

### Getting Help

**If you encounter issues:**
1. Check the **system status indicators** in the sidebar
2. Visit **http://localhost:8000/health** for detailed diagnostics
3. Consult the **[Troubleshooting FAQ](troubleshooting_faq.md)** for specific solutions
4. Review the **[User Manual](user_manual.md)** for detailed guidance

---

## 💡 Tips for Success

### Document Selection

**Best documents for learning:**
- Well-structured PDFs with clear text
- Documents you're familiar with (easier to verify answers)
- Medium-sized files (5-20 pages) for reasonable processing time
- Content-rich documents with facts and details

### Question Strategies

**Effective first questions:**
- Start broad: "What is this document about?"
- Get specific: "What does it say about [specific topic]?"
- Ask for structure: "What are the main sections?"
- Request summaries: "Summarize the key findings"

**Questions to avoid initially:**
- Very complex multi-part questions
- Questions requiring information not in your documents
- Questions that are too vague or general

### Building Your Knowledge Base

**Smart document organization:**
- Upload related documents together
- Use descriptive filenames
- Start with high-quality, well-formatted documents
- Gradually add more content as you learn the system

---

**🎊 Congratulations!** You've successfully set up and used your RAG system. You now have a powerful, private AI assistant that can help you understand and analyze your documents.

**Next:** Explore the [User Manual](user_manual.md) to discover all the advanced features and capabilities available to you.

---

**Last Updated:** August 4, 2025  
**Tutorial Version:** 1.0  
**Estimated Completion Time:** 5-10 minutes