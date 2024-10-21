#!/bin/bash

# Run the Python script
python /Users/waterstk/Documents/GitHub/thomas-k-waters.github.io/add_papers_to_website.py

# Check if the flag file exists
if [ -f /tmp/new_papers_added.flag ]; then
    # Send an email notification
    SUBJECT="New Papers Added to Website"
    BODY="New papers have been added to your website."
    TO="thomas.k.waters@gmail.com"
    echo "$BODY" | mail -s "$SUBJECT" "$TO"
    
    # Remove the flag file
    rm /tmp/new_papers_added.flag
fi
