const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');

const app = express();
const port = 3000;

// Set up Multer for file uploads
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        // Ensure the directory exists
        const dir = '/home/sibo-t/work/help/Backend_ImmersiPay/auth/';
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
        }
        cb(null, dir);
    },
    filename: (req, file, cb) => {
        // Create a unique filename with a timestamp
        cb(null, file.fieldname + '-' + Date.now() + path.extname(file.originalname));
    }
});

const upload = multer({ storage: storage });

// Serve the HTML file
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// Handle the POST request from the client
app.post('/save-image', upload.single('photo'), (req, res) => {
    if (!req.file) {
        return res.status(400).send('No file uploaded.');
    }
    // Respond with the path where the file was saved
    res.json({ 
        message: 'Image saved successfully!', 
        filePath: req.file.path
    });
});

app.listen(port, () => {
    console.log(`Server listening at http://localhost:${port}`);
});