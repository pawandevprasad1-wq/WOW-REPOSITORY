// ==================== IMPORTS ====================
const express = require('express');
const mongoose = require('mongoose');
const cloudinary = require('cloudinary').v2;
const multer = require('multer');
const cors = require('cors');

const app = express();

// ==================== MIDDLEWARE ====================
app.use(cors());
app.use(express.json());

const storage = multer.memoryStorage();
const upload = multer({ storage: storage });

// ==================== CONFIGURATION DETAILS ====================

// MongoDB URI (Database Name: WOW सेट किया गया है)
const MONGO_URI = process.env.MONGO_URI || "mongodb+srv://pawandevprasad1_db_user:12345@cluster0.acobnxp.mongodb.net/WOW?retryWrites=true&w=majority&appName=Cluster0";

// Cloudinary Credentials
cloudinary.config({
  cloud_name: process.env.CLOUDINARY_CLOUD_NAME || 'pfwjg7ip',
  api_key: process.env.CLOUDINARY_API_KEY || '368463435529631',
  api_secret: process.env.CLOUDINARY_API_SECRET || '6u71nfiRo4ikkXSR_G02iUt5tM'
});

// ==================== MONGODB CONNECTION ====================
mongoose.connect(MONGO_URI)
  .then(() => console.log('MongoDB (WOW Database) से कनेक्ट हो गया!'))
  .catch((err) => console.error('MongoDB कनेक्शन एरर:', err));

// MongoDB Schema - Collection Name explicitly set to 'WOW'
const AudioSchema = new mongoose.Schema({
  audioUrl: String,
  createdAt: { type: Date, default: Date.now }
}, { collection: 'WOW' });

const Audio = mongoose.model('Audio', AudioSchema);

// ==================== UPLOAD ROUTE ====================
app.post('/upload-audio', upload.single('audio'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'ऑडियो फाइल नहीं मिली' });
    }

    // Cloudinary पर ऑडियो अपलोड करना
    const uploadStream = cloudinary.uploader.upload_stream(
      { resource_type: 'video', folder: 'voice_recordings' },
      async (error, result) => {
        if (error) {
          console.error('Cloudinary एरर:', error);
          return res.status(500).json({ error: error.message });
        }

        // MongoDB (WOW Collection) में URL सेव करना
        const newAudio = new Audio({ audioUrl: result.secure_url });
        await newAudio.save();

        console.log('ऑडियो WOW कलेक्शन में सेव हुआ:', result.secure_url);
        return res.json({ message: 'सफलतापूर्वक सेव हो गया', url: result.secure_url });
      }
    );

    uploadStream.end(req.file.buffer);
  } catch (err) {
    console.error('सर्वर एरर:', err);
    res.status(500).json({ error: err.message });
  }
});

// ==================== SERVER LISTEN ====================
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`सर्वर पोर्ट ${PORT} पर सक्रिय है`);
});
