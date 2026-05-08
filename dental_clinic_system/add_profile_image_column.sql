-- Add profile_image column to staff table for user profile pictures
-- Run this SQL in your MySQL database (phpMyAdmin, MySQL Workbench, or command line)

USE dental_clinic_system;

-- Add profile_image column to staff table if it doesn't exist
ALTER TABLE staff ADD COLUMN profile_image VARCHAR(500) DEFAULT NULL AFTER staff_name;

-- Verify the column was added
DESCRIBE staff;

-- Check if the column was added
SELECT * FROM staff;
