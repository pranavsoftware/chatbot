const nodemailer = require("nodemailer");
require("dotenv").config();

const email = process.argv[2];
const otp = process.argv[3];

let transporter = nodemailer.createTransport({
    service: "gmail",
    auth: {
        user: process.env.OTP_EMAIL,
        pass: process.env.OTP_PASS,
    },
});

let mailOptions = {
    from: `"Chat Bot-Project" <${process.env.OTP_EMAIL}>`,
    to: email,
    subject: "Your OTP Code",
    html: `
        <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ccc; border-radius: 10px;">
            <h2 style="color: #4A90E2;">Chat Bot</h2>
            <p>Hi,</p>
            <p>Your OTP code is:</p>
            <h1 style="background: #f0f0f0; display: inline-block; padding: 10px 20px; border-radius: 5px;">${otp}</h1>
            <p>This OTP is valid for a limited time. Do not share it with anyone.</p>
            <hr />
            <p style="font-size: 0.9em; color: #777;">
                Made by <strong>Pranav Rayban</strong><br />
                <a href="linkedin.com/in/pranav-rayban-vit2027" target="_blank" style="text-decoration: none; color: #0e76a8;">
                    <img src="https://cdn-icons-png.flaticon.com/512/174/174857.png" alt="LinkedIn" style="width: 16px; height: 16px; vertical-align: middle;" />
                    LinkedIn
                </a>
            </p>
        </div>
    `,
};

transporter.sendMail(mailOptions, function (error, info) {
    if (error) {
        console.log("Error sending OTP:", error);
    } else {
        console.log("OTP email sent:", info.response);
    }
});
