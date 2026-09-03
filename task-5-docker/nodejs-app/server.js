const express = require('express');

const app = express();
const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => {
  res.send(`
    <html>
      <head><title>Node.js Hello World</title></head>
      <body style="font-family: sans-serif; text-align: center; margin-top: 15vh;">
        <h1>Hello World</h1>
        <p>Served by Node.js and Express inside Docker</p>
      </body>
    </html>
  `);
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Node.js app listening on port ${PORT}`);
});
