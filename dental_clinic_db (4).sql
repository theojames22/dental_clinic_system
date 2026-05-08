-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: May 07, 2026 at 11:50 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `dental_clinic_db`
--

DELIMITER $$
--
-- Procedures
--
CREATE DEFINER=`root`@`localhost` PROCEDURE `add_appointment` (IN `p_patient_id` INT, IN `p_appointment_date` DATETIME, IN `p_is_walkin` BOOLEAN)   BEGIN
    IF p_is_walkin THEN
        SET @next_queue = (
            SELECT IFNULL(MAX(queue_number), 0) + 1 
            FROM appointments 
            WHERE DATE(appointment_date) = DATE(p_appointment_date)
        );

        INSERT INTO appointments (patient_id, appointment_date, status, queue_number)
        VALUES (p_patient_id, p_appointment_date, 'walk-in', @next_queue);
    ELSE
        INSERT INTO appointments (patient_id, appointment_date, status)
        VALUES (p_patient_id, p_appointment_date, 'scheduled');
    END IF;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `add_treatment` (IN `p_appointment_id` INT, IN `p_treatment_name` VARCHAR(100))   BEGIN
    INSERT INTO treatments (appointment_id, treatment_name, cost)
    SELECT 
        p_appointment_id,
        treatment_name,
        default_cost
    FROM treatment_types
    WHERE treatment_name = p_treatment_name;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `complete_appointment` (IN `app_id` INT)   BEGIN
    UPDATE appointments 
    SET status = 'completed' 
    WHERE appointment_id = app_id;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `GetInventoryAlerts` ()   BEGIN
                SELECT 
                    item_id,
                    item_name,
                    quantity,
                    reorder_level,
                    CASE 
                        WHEN quantity = 0 THEN 'Out of Stock'
                        WHEN quantity <= reorder_level THEN 'Low Stock'
                        ELSE 'Sufficient'
                    END as alert_level,
                    (reorder_level - quantity) as units_to_order
                FROM inventory
                WHERE quantity <= reorder_level * 2
                ORDER BY quantity ASC;
            END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `login_user` (IN `p_username` VARCHAR(50), IN `p_password` VARCHAR(100))   BEGIN
    SELECT user_id, username, role
    FROM users
    WHERE username = p_username AND password = p_password;
END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `pay_bill` (IN `p_bill_id` INT)   BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SELECT 'Payment failed' AS message;
    END;

    START TRANSACTION;

    UPDATE billing
    SET status = 'Paid',
        payment_date = NOW()
    WHERE bill_id = p_bill_id;

    COMMIT;

    SELECT 'Payment successful' AS message;

END$$

CREATE DEFINER=`root`@`localhost` PROCEDURE `restock_item` (IN `p_item_id` INT, IN `p_qty` INT)   BEGIN
    UPDATE inventory
    SET quantity = quantity + p_qty
    WHERE item_id = p_item_id;
END$$

DELIMITER ;

-- --------------------------------------------------------

--
-- Table structure for table `appointments`
--

CREATE TABLE `appointments` (
  `appointment_id` int(11) NOT NULL,
  `patient_id` int(11) DEFAULT NULL,
  `appointment_date` datetime DEFAULT NULL,
  `status` enum('scheduled','completed','cancelled','walk-in') DEFAULT 'scheduled',
  `treatment_type_id` int(11) DEFAULT NULL,
  `staff_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Triggers `appointments`
--
DELIMITER $$
CREATE TRIGGER `trg_create_billing` AFTER UPDATE ON `appointments` FOR EACH ROW BEGIN
    IF NEW.status = 'completed' AND OLD.status <> 'completed' THEN
        INSERT INTO billing (appointment_id, amount, status)
        VALUES (NEW.appointment_id, 0, 'Pending');
    END IF;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Stand-in structure for view `appointment_info`
-- (See below for the actual view)
--
CREATE TABLE `appointment_info` (
`patient_name` varchar(100)
,`age` int(11)
,`gender` varchar(50)
,`contact` varchar(20)
,`address` varchar(255)
,`appointment_date` datetime
,`treatment_name` varchar(100)
,`staff_name` varchar(100)
,`status` enum('scheduled','completed','cancelled','walk-in')
);

-- --------------------------------------------------------

--
-- Stand-in structure for view `appointment_report`
-- (See below for the actual view)
--
CREATE TABLE `appointment_report` (
`appointment_id` int(11)
,`patient_name` varchar(100)
,`dentist_name` varchar(18)
,`appointment_date` datetime
,`status` enum('scheduled','completed','cancelled','walk-in')
);

-- --------------------------------------------------------

--
-- Stand-in structure for view `appointment_union`
-- (See below for the actual view)
--
CREATE TABLE `appointment_union` (
`appointment_id` int(11)
,`appointment_date` datetime
,`type` varchar(9)
);

-- --------------------------------------------------------

--
-- Table structure for table `billing`
--

CREATE TABLE `billing` (
  `bill_id` int(11) NOT NULL,
  `appointment_id` int(11) DEFAULT NULL,
  `amount` decimal(10,2) DEFAULT NULL,
  `status` enum('Pending','Paid','Partial') DEFAULT 'Pending',
  `payment_date` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Triggers `billing`
--
DELIMITER $$
CREATE TRIGGER `billing_payment_date_trigger` BEFORE UPDATE ON `billing` FOR EACH ROW BEGIN
    IF NEW.status = 'Paid' AND OLD.status != 'Paid' THEN
        SET NEW.payment_date = NOW();
    END IF;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Stand-in structure for view `billing_report`
-- (See below for the actual view)
--
CREATE TABLE `billing_report` (
`bill_id` int(11)
,`patient_name` varchar(100)
,`amount` decimal(10,2)
,`status` enum('Pending','Paid','Partial')
,`payment_date` datetime
);

-- --------------------------------------------------------

--
-- Stand-in structure for view `full_report`
-- (See below for the actual view)
--
CREATE TABLE `full_report` (
`patient_name` varchar(100)
,`appointment_date` datetime
,`appointment_status` enum('scheduled','completed','cancelled','walk-in')
,`amount` decimal(10,2)
,`billing_status` enum('Pending','Paid','Partial')
);

-- --------------------------------------------------------

--
-- Table structure for table `inventory`
--

CREATE TABLE `inventory` (
  `item_id` int(11) NOT NULL,
  `item_name` varchar(100) DEFAULT NULL,
  `quantity` int(11) DEFAULT NULL,
  `price` decimal(10,2) DEFAULT NULL,
  `reorder_level` int(11) DEFAULT NULL,
  `image` mediumblob DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `inventory`
--

INSERT INTO `inventory` (`item_id`, `item_name`, `quantity`, `price`, `reorder_level`, `image`) VALUES
(1, 'Anesthesia', 35, 200.00, 10, NULL),
(2, 'Gloves', 120, 5.00, 20, NULL);

--
-- Triggers `inventory`
--
DELIMITER $$
CREATE TRIGGER `inventory_alert` AFTER UPDATE ON `inventory` FOR EACH ROW BEGIN
    IF NEW.quantity <= NEW.reorder_level THEN
        INSERT INTO inventory_log(item_id, message, log_date)
        VALUES (NEW.item_id, 'Low stock detected', NOW());
    END IF;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Stand-in structure for view `inventory_report`
-- (See below for the actual view)
--
CREATE TABLE `inventory_report` (
`item_id` int(11)
,`item_name` varchar(100)
,`quantity` int(11)
,`reorder_level` int(11)
,`alert_status` varchar(16)
);

-- --------------------------------------------------------

--
-- Stand-in structure for view `monthly_sales_report`
-- (See below for the actual view)
--
CREATE TABLE `monthly_sales_report` (
`month` varchar(7)
,`total_sales` decimal(32,2)
,`total_transactions` bigint(21)
);

-- --------------------------------------------------------

--
-- Table structure for table `patient`
--

CREATE TABLE `patient` (
  `patient_id` int(11) NOT NULL,
  `patient_name` varchar(100) DEFAULT NULL,
  `contact` varchar(20) DEFAULT NULL,
  `medical_history` text DEFAULT NULL,
  `registration_date` date DEFAULT curdate(),
  `age` int(11) DEFAULT NULL,
  `gender` varchar(50) DEFAULT NULL,
  `address` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Stand-in structure for view `patient_history`
-- (See below for the actual view)
--
CREATE TABLE `patient_history` (
`patient_name` varchar(100)
,`appointment_date` datetime
,`status` enum('scheduled','completed','cancelled','walk-in')
,`treatment_name` varchar(100)
,`cost` decimal(10,2)
);

-- --------------------------------------------------------

--
-- Table structure for table `staff`
--

CREATE TABLE `staff` (
  `staff_id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `staff_name` varchar(100) DEFAULT NULL,
  `profile_image` varchar(500) DEFAULT NULL,
  `role` enum('dentist','admin','receptionist') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `staff`
--

INSERT INTO `staff` (`staff_id`, `user_id`, `staff_name`, `profile_image`, `role`) VALUES
(7, 12, 'theojames', NULL, 'admin'),
(8, 13, 'receptionist', NULL, 'receptionist'),
(9, 14, 'dentist', NULL, 'dentist');

-- --------------------------------------------------------

--
-- Table structure for table `treatment_types`
--

CREATE TABLE `treatment_types` (
  `treatment_type_id` int(11) NOT NULL,
  `treatment_name` varchar(100) DEFAULT NULL,
  `cost` decimal(10,2) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `treatment_types`
--

INSERT INTO `treatment_types` (`treatment_type_id`, `treatment_name`, `cost`) VALUES
(1, 'Consultation', 500.00),
(2, 'Dental Cleaning', 800.00),
(3, 'Tooth Extraction', 1000.00),
(7, 'brace adjustment', 1500.00),
(8, 'Tooth Ache', 50.00);

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `user_id` int(11) NOT NULL,
  `username` varchar(50) DEFAULT NULL,
  `password` varchar(50) NOT NULL,
  `password_hash` varchar(100) DEFAULT NULL,
  `login_date` date DEFAULT NULL,
  `role` enum('admin','receptionist','dentist') DEFAULT 'receptionist',
  `email` varchar(255) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `reset_code` varchar(10) DEFAULT NULL,
  `reset_code_expiration` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`user_id`, `username`, `password`, `password_hash`, `login_date`, `role`, `email`, `phone`, `reset_code`, `reset_code_expiration`) VALUES
(12, 'admin', '', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', NULL, 'admin', 'theojamesnicdao22@gmail.com', NULL, NULL, NULL),
(13, 'receptionist', '', 'a27dce9d8b5488238487ca36967563b7487b12232e3d1cb98442360f033cfbd7', NULL, 'receptionist', 'theojamesnicdao26@gmail.com', NULL, NULL, NULL),
(14, 'dentist', '', '8906f3eab9db42dab58fea419e13d61905334d00eb32635d5523026dbe18ad31', NULL, 'dentist', 'theojamesnicdao21@gmail.com', NULL, NULL, NULL);

-- --------------------------------------------------------

--
-- Structure for view `appointment_info`
--
DROP TABLE IF EXISTS `appointment_info`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `appointment_info`  AS SELECT `p`.`patient_name` AS `patient_name`, `p`.`age` AS `age`, `p`.`gender` AS `gender`, `p`.`contact` AS `contact`, `p`.`address` AS `address`, `a`.`appointment_date` AS `appointment_date`, `t`.`treatment_name` AS `treatment_name`, `s`.`staff_name` AS `staff_name`, `a`.`status` AS `status` FROM (((`patient` `p` join `appointments` `a` on(`p`.`patient_id` = `a`.`patient_id`)) join `treatment_types` `t` on(`a`.`treatment_type_id` = `t`.`treatment_type_id`)) join `staff` `s` on(`a`.`staff_id` = `s`.`staff_id`)) ;

-- --------------------------------------------------------

--
-- Structure for view `appointment_report`
--
DROP TABLE IF EXISTS `appointment_report`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `appointment_report`  AS SELECT `a`.`appointment_id` AS `appointment_id`, `p`.`patient_name` AS `patient_name`, 'Dr. Liezel Cabacis' AS `dentist_name`, `a`.`appointment_date` AS `appointment_date`, `a`.`status` AS `status` FROM (`appointments` `a` join `patient` `p` on(`a`.`patient_id` = `p`.`patient_id`)) ;

-- --------------------------------------------------------

--
-- Structure for view `appointment_union`
--
DROP TABLE IF EXISTS `appointment_union`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `appointment_union`  AS SELECT `appointments`.`appointment_id` AS `appointment_id`, `appointments`.`appointment_date` AS `appointment_date`, 'Scheduled' AS `type` FROM `appointments` WHERE `appointments`.`status` = 'scheduled'union select `appointments`.`appointment_id` AS `appointment_id`,`appointments`.`appointment_date` AS `appointment_date`,'Walk-in' AS `type` from `appointments` where `appointments`.`status` = 'walk-in'  ;

-- --------------------------------------------------------

--
-- Structure for view `billing_report`
--
DROP TABLE IF EXISTS `billing_report`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `billing_report`  AS SELECT `b`.`bill_id` AS `bill_id`, `p`.`patient_name` AS `patient_name`, `b`.`amount` AS `amount`, `b`.`status` AS `status`, `b`.`payment_date` AS `payment_date` FROM ((`billing` `b` join `appointments` `a` on(`b`.`appointment_id` = `a`.`appointment_id`)) join `patient` `p` on(`a`.`patient_id` = `p`.`patient_id`)) ;

-- --------------------------------------------------------

--
-- Structure for view `full_report`
--
DROP TABLE IF EXISTS `full_report`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `full_report`  AS SELECT `p`.`patient_name` AS `patient_name`, `a`.`appointment_date` AS `appointment_date`, `a`.`status` AS `appointment_status`, `b`.`amount` AS `amount`, `b`.`status` AS `billing_status` FROM ((`appointments` `a` left join `billing` `b` on(`a`.`appointment_id` = `b`.`appointment_id`)) join `patient` `p` on(`a`.`patient_id` = `p`.`patient_id`)) ;

-- --------------------------------------------------------

--
-- Structure for view `inventory_report`
--
DROP TABLE IF EXISTS `inventory_report`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `inventory_report`  AS SELECT `inventory`.`item_id` AS `item_id`, `inventory`.`item_name` AS `item_name`, `inventory`.`quantity` AS `quantity`, `inventory`.`reorder_level` AS `reorder_level`, CASE WHEN `inventory`.`quantity` <= `inventory`.`reorder_level` THEN 'Reorder Needed' ELSE 'Sufficient Stock' END AS `alert_status` FROM `inventory` ;

-- --------------------------------------------------------

--
-- Structure for view `monthly_sales_report`
--
DROP TABLE IF EXISTS `monthly_sales_report`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `monthly_sales_report`  AS SELECT date_format(`billing`.`payment_date`,'%Y-%m') AS `month`, sum(`billing`.`amount`) AS `total_sales`, count(`billing`.`bill_id`) AS `total_transactions` FROM `billing` WHERE `billing`.`status` = 'Paid' GROUP BY date_format(`billing`.`payment_date`,'%Y-%m') ;

-- --------------------------------------------------------

--
-- Structure for view `patient_history`
--
DROP TABLE IF EXISTS `patient_history`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `patient_history`  AS SELECT `p`.`patient_name` AS `patient_name`, `a`.`appointment_date` AS `appointment_date`, `a`.`status` AS `status`, `t`.`treatment_name` AS `treatment_name`, `t`.`cost` AS `cost` FROM ((`patient` `p` join `appointments` `a` on(`p`.`patient_id` = `a`.`patient_id`)) left join `treatment_types` `t` on(`a`.`treatment_type_id` = `t`.`treatment_type_id`)) ;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `appointments`
--
ALTER TABLE `appointments`
  ADD PRIMARY KEY (`appointment_id`),
  ADD KEY `patient_id` (`patient_id`),
  ADD KEY `fk_treatment_type` (`treatment_type_id`),
  ADD KEY `fk_staff` (`staff_id`);

--
-- Indexes for table `billing`
--
ALTER TABLE `billing`
  ADD PRIMARY KEY (`bill_id`),
  ADD KEY `appointment_id` (`appointment_id`);

--
-- Indexes for table `inventory`
--
ALTER TABLE `inventory`
  ADD PRIMARY KEY (`item_id`);

--
-- Indexes for table `patient`
--
ALTER TABLE `patient`
  ADD PRIMARY KEY (`patient_id`);

--
-- Indexes for table `staff`
--
ALTER TABLE `staff`
  ADD PRIMARY KEY (`staff_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `treatment_types`
--
ALTER TABLE `treatment_types`
  ADD PRIMARY KEY (`treatment_type_id`),
  ADD UNIQUE KEY `treatment_name` (`treatment_name`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD KEY `idx_reset_code` (`reset_code`,`reset_code_expiration`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `appointments`
--
ALTER TABLE `appointments`
  MODIFY `appointment_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;

--
-- AUTO_INCREMENT for table `billing`
--
ALTER TABLE `billing`
  MODIFY `bill_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `inventory`
--
ALTER TABLE `inventory`
  MODIFY `item_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `patient`
--
ALTER TABLE `patient`
  MODIFY `patient_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- AUTO_INCREMENT for table `staff`
--
ALTER TABLE `staff`
  MODIFY `staff_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT for table `treatment_types`
--
ALTER TABLE `treatment_types`
  MODIFY `treatment_type_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `appointments`
--
ALTER TABLE `appointments`
  ADD CONSTRAINT `appointments_ibfk_1` FOREIGN KEY (`patient_id`) REFERENCES `patient` (`patient_id`),
  ADD CONSTRAINT `fk_staff` FOREIGN KEY (`staff_id`) REFERENCES `staff` (`staff_id`),
  ADD CONSTRAINT `fk_treatment_type` FOREIGN KEY (`treatment_type_id`) REFERENCES `treatment_types` (`treatment_type_id`);

--
-- Constraints for table `billing`
--
ALTER TABLE `billing`
  ADD CONSTRAINT `billing_ibfk_1` FOREIGN KEY (`appointment_id`) REFERENCES `appointments` (`appointment_id`);

--
-- Constraints for table `staff`
--
ALTER TABLE `staff`
  ADD CONSTRAINT `staff_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
