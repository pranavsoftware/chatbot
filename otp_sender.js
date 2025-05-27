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
    from: process.env.OTP_EMAIL,
    to: email,
    subject: "Your OTP Code",
    text: `Your OTP code is ${otp}`,
};

transporter.sendMail(mailOptions, function(error, info){
    if (error) {
        console.log(error);
    }
});
