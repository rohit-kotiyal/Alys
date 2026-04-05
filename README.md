# 🎯 Alys - AI Data Analyst Dashboard

AI-powered analytics dashboard that lets you upload CSV files and ask questions in natural language.

## 🛠️ Tech Stack

**Backend:**
- FastAPI 0.135.3
- Pandas 3.0.2
- OpenAI API (Week 2)

**Frontend:** (Coming Soon)
- React.js
- Tailwind CSS
- Recharts

## 📦 Installation 
### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Variables

Create `backend/.env`:
```env
UPLOAD_FOLDER=uploads
MAX_FILE_SIZE=10485760
ALLOWED_EXTENSIONS=csv
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Run Server
```bash
uvicorn main:app --reload
```

Visit: http://localhost:8000/docs

## 🗓️ Development Roadmap

### Week 1 - Core Data Processing
- [x] Day 1-2: FastAPI Setup ✅
- [ ] Day 3-4: CSV Upload & Validation
- [ ] Day 5-6: Pandas Data Analysis
- [ ] Day 7: Chart Integration

### Week 2 - AI Integration
- [ ] Day 8-9: AI Query Understanding
- [ ] Day 10-11: Dynamic Pandas Execution
- [ ] Day 12: Insight Generation
- [ ] Day 13: Chat UI
- [ ] Day 14: Deployment

## 📄 License

MIT

## 👨‍💻 Author

**RUDY** - Built as a learning project following a 14-day roadmap.