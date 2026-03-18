# How to Use Claude Code — วิธีใช้ Claude Code

Claude Code is a command-line tool that brings AI directly to your terminal. เป็นเครื่องมือที่ช่วยให้นักพัฒนาทำงานได้เร็วขึ้นด้วย AI ในเทอร์มินัล

## Getting Started — เริ่มต้นใช้งาน

### Installation — การติดตั้ง

1. Install via npm: `npm install -g @anthropic-ai/claude-code`
2. Set your API key: `export ANTHROPIC_API_KEY=your-key`
3. Run `claude` in any project directory

ขั้นตอนง่ายมากค่ะ แค่ 3 ขั้นตอนก็เริ่มใช้งานได้เลย

### Key Features — ฟีเจอร์หลัก

| Feature | Description | คำอธิบาย |
|---------|-------------|----------|
| Code editing | Edit files with natural language | แก้ไขไฟล์ด้วยภาษาธรรมชาติ |
| Git integration | Commit, push, create PRs | จัดการ Git ได้ในตัว |
| Multi-file search | Find code across your project | ค้นหาโค้ดทั้งโปรเจค |
| Shell commands | Run terminal commands safely | รันคำสั่งเทอร์มินัลอย่างปลอดภัย |

## Best Practices — แนวปฏิบัติที่ดี

- **Be specific**: Tell Claude exactly what you want — บอกให้ชัดเจนว่าต้องการอะไร
- **Use context**: Reference file paths and function names — อ้างอิงชื่อไฟล์และฟังก์ชัน
- **Review changes**: Always review before committing — ตรวจสอบก่อน commit เสมอ
- **Iterate**: Ask for adjustments if needed — ขอปรับแก้ได้ถ้ายังไม่พอใจ

> Claude Code สามารถช่วยงาน engineering ได้ตั้งแต่ bug fix ไปจนถึง feature development ทั้งหมดผ่าน command line ที่คุ้นเคย

### Performance Comparison — เปรียบเทียบประสิทธิภาพ

| Metric | Manual | With Claude Code | Improvement |
|--------|--------|------------------|-------------|
| Bug fix time | 45 min | 10 min | 4.5x faster |
| Code review | 30 min | 8 min | 3.75x faster |
| Documentation | 60 min | 15 min | 4x faster |
| Test writing | 40 min | 12 min | 3.3x faster |

### Example Commands — ตัวอย่างคำสั่ง

```
claude "fix the login bug in auth.py"
claude "add unit tests for the User model"
claude "refactor this function to use async/await"
```

---

## Summary — สรุป

Claude Code ช่วยให้ทำงาน software engineering ได้เร็วขึ้น 3-5 เท่า โดยไม่ต้องออกจาก terminal ที่คุ้นเคย ลองใช้ดูแล้วจะติดใจค่ะ
