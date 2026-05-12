#!/bin/bash
cd "C:/Projects/AutoClicker"
git init
git add .
git commit -m "Initial commit - AutoClicker v1.0"
git branch -M main
git remote add origin git@github.com:mickymac3603-coder/ProjectAutoclick.git
git push -u origin main
echo "Done! Check your GitHub repo."
