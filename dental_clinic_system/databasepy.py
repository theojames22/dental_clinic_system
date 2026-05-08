from mysql.connector import connect, Error
import hashlib
from datetime import datetime
from dashboard_gui.style import Config

class Database:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        try:
            self.connection = connect(
                host=Config.DB_HOST,
                database=Config.DB_NAME,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD
            )
            return True
        except Error as e:
            print(f"Database connection error: {e}")
            return False
    
    def is_connected(self):
        return self.connection is not None and self.connection.is_connected()
    
    def execute_query(self, query, params=None):
        cursor = None
        try:
            if not self.is_connected():
                self.connect()
            
            cursor = self.connection.cursor(dictionary=True)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            query_upper = query.strip().upper()
            if query_upper.startswith('SELECT') or query_upper.startswith('WITH'):
                return cursor.fetchall()
            elif query_upper.startswith('CALL'):
                result = []
                for result_set in cursor.fetchall():
                    result.append(result_set)
                return result
            else:
                self.connection.commit()
                return cursor.lastrowid if cursor.lastrowid else True
        except Error as e:
            print(f"Query error: {e}")
            if self.connection:
                self.connection.rollback()
            return None
        finally:
            if cursor:
                cursor.close()
    
    def call_procedure(self, procedure_name, params=None):
        try:
            if params:
                placeholders = ','.join(['%s'] * len(params))
                query = f"CALL {procedure_name}({placeholders})"
                result = self.execute_query(query, params)
            else:
                query = f"CALL {procedure_name}()"
                result = self.execute_query(query)
            return result
        except Error as e:
            print(f"Procedure call error: {e}")
            return None
        
    def get_recent_activities(self, limit=5):
        query = """
            SELECT 
                TIME_FORMAT(a.appointment_date, '%h:%i %p') as time,
                DATE_FORMAT(a.appointment_date, '%Y-%m-%d') as date,
                a.status,
                p.patient_name,
                COALESCE(s.staff_name, 'System') as user,
                a.appointment_date as sort_date
            FROM appointments a
            JOIN patient p ON a.patient_id = p.patient_id
            LEFT JOIN staff s ON s.role = 'receptionist'
            WHERE a.appointment_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            ORDER BY a.appointment_date DESC
            LIMIT %s
        """
        result = self.execute_query(query, (limit,))
        
        if not result:
            return []
        
        activities = []
        for row in result:
            status_map = {
                'completed': 'Appointment completed',
                'scheduled': 'New appointment scheduled',
                'walk-in': 'Walk-in patient arrived',
                'cancelled': 'Appointment cancelled'
            }
            
            action = f"{status_map.get(row['status'], 'Appointment updated')} for {row['patient_name']}"
            
            activities.append({
                'time': row['time'],
                'date': row['date'],
                'action': action,
                'user': row['user']
            })
        
        return activities

    def get_appointment_info_view(self):
        query = "SELECT * FROM appointment_info ORDER BY appointment_date DESC"
        return self.execute_query(query) or []

    def get_patient_by_name_contact(self, patient_name, contact):
        query = "SELECT patient_id, patient_name, age, gender, contact, address FROM patient WHERE patient_name = %s AND contact = %s"
        result = self.execute_query(query, (patient_name, contact))
        return result[0] if result else None

    def create_patient_with_details(self, patient_name, age, gender, contact, address):
        query = """
            INSERT INTO patient (patient_name, age, gender, contact, address, registration_date)
            VALUES (%s, %s, %s, %s, %s, CURDATE())
        """
        return self.execute_query(query, (patient_name, age, gender, contact, address))

    def get_all_appointments(self):
        query = """
            SELECT a.appointment_id, a.appointment_date, a.status, s.staff_name as doctor_name, p.patient_name
            FROM appointments a
            JOIN patient p ON a.patient_id = p.patient_id
            JOIN staff s ON a.staff_id = s.staff_id
            ORDER BY a.appointment_date DESC
        """
        return self.execute_query(query) or []

    def get_appointments_by_status(self, status):
        query = """
            SELECT a.appointment_id, a.appointment_date, a.status, s.staff_name as doctor_name, p.patient_name
            FROM appointments a
            JOIN patient p ON a.patient_id = p.patient_id
            JOIN staff s ON a.staff_id = s.staff_id
            WHERE a.status = %s
            ORDER BY a.appointment_date DESC
        """
        return self.execute_query(query, (status,)) or []

    def get_appointment_details(self, appointment_id):
        query = """
            SELECT a.*, p.patient_name, p.patient_id, p.age, p.gender, p.contact, p.address
            FROM appointments a
            JOIN patient p ON a.patient_id = p.patient_id
            WHERE a.appointment_id = %s
        """
        result = self.execute_query(query, (appointment_id,))
        return result[0] if result else None

    def get_treatments_for_appointment(self, appointment_id):
        query = """
            SELECT tt.treatment_type_id, tt.treatment_name, tt.cost
            FROM appointments a
            JOIN treatment_types tt ON a.treatment_type_id = tt.treatment_type_id
            WHERE a.appointment_id = %s
        """
        return self.execute_query(query, (appointment_id,)) or []

    def get_all_patients(self):
        query = "SELECT * FROM patient ORDER BY registration_date DESC"
        return self.execute_query(query) or []

    def get_patient_details(self, patient_id):
        query = "SELECT * FROM patient WHERE patient_id = %s"
        result = self.execute_query(query, (patient_id,))
        return result[0] if result else None

    def get_patient_visit_count(self, patient_id):
        query = "SELECT COUNT(*) as count FROM appointments WHERE patient_id = %s"
        result = self.execute_query(query, (patient_id,))
        return result[0]['count'] if result else 0

    def get_patient_treatment_history(self, patient_id):
        query = """
            SELECT tt.treatment_name, tt.cost, a.appointment_date
            FROM appointments a
            JOIN treatment_types tt ON a.treatment_type_id = tt.treatment_type_id
            WHERE a.patient_id = %s
            ORDER BY a.appointment_date DESC
        """
        return self.execute_query(query, (patient_id,)) or []

    def search_patients(self, search_term):
        query = """
            SELECT * FROM patient 
            WHERE patient_name LIKE %s OR contact LIKE %s
            ORDER BY patient_name
        """
        search_pattern = f"%{search_term}%"
        return self.execute_query(query, (search_pattern, search_pattern)) or []

    def update_patient(self, patient_id, patient_name, contact, medical_history):
        query = """
            UPDATE patient 
            SET patient_name = %s, contact = %s, medical_history = %s
            WHERE patient_id = %s
        """
        return self.execute_query(query, (patient_name, contact, medical_history, patient_id))

    def delete_patient(self, patient_id):
        query = "DELETE FROM patient WHERE patient_id = %s"
        return self.execute_query(query, (patient_id,))

    def update_appointment(self, appointment_id, patient_id, appointment_date, status, staff_id=None, treatment_name=None, treatment_cost=0):
        try:
            if not self.is_connected():
                self.connect()
            
            cursor = self.connection.cursor(dictionary=True)
            
            try:
                if not self.connection.in_transaction:
                    self.connection.start_transaction()
                
                treatment_type_id = None
                if treatment_name:
                    cursor.execute("SELECT treatment_type_id FROM treatment_types WHERE treatment_name = %s", (treatment_name,))
                    existing = cursor.fetchone()
                    
                    if existing:
                        treatment_type_id = existing['treatment_type_id']
                    else:
                        cursor.execute("INSERT INTO treatment_types (treatment_name, cost) VALUES (%s, %s)", 
                                      (treatment_name, treatment_cost))
                        treatment_type_id = cursor.lastrowid
                
                if staff_id is None:
                    cursor.execute("SELECT staff_id FROM staff WHERE role = 'dentist' LIMIT 1")
                    staff_result = cursor.fetchone()
                    staff_id = staff_result['staff_id'] if staff_result else None
                
                if treatment_type_id:
                    query = """
                        UPDATE appointments 
                        SET patient_id = %s, appointment_date = %s, status = %s, staff_id = %s, treatment_type_id = %s
                        WHERE appointment_id = %s
                    """
                    cursor.execute(query, (patient_id, appointment_date, status, staff_id, treatment_type_id, appointment_id))
                else:
                    query = """
                        UPDATE appointments 
                        SET patient_id = %s, appointment_date = %s, status = %s, staff_id = %s
                        WHERE appointment_id = %s
                    """
                    cursor.execute(query, (patient_id, appointment_date, status, staff_id, appointment_id))
                
                if treatment_type_id:
                    cursor.execute("SELECT cost FROM treatment_types WHERE treatment_type_id = %s", (treatment_type_id,))
                    cost_result = cursor.fetchone()
                    total_cost = cost_result['cost'] if cost_result else 0
                    
                    update_billing = """
                        UPDATE billing 
                        SET amount = %s
                        WHERE appointment_id = %s
                    """
                    cursor.execute(update_billing, (total_cost, appointment_id))
                
                self.connection.commit()
                return True
                
            except Exception as e:
                if self.connection.in_transaction:
                    self.connection.rollback()
                print(f"Transaction error in update_appointment: {e}")
                return False
            finally:
                cursor.close()
                
        except Exception as e:
            print(f"Error in update_appointment: {e}")
            return False
        

    # ═══════════════════════════════════════════════════════════════════
    # PATIENTS PAGE QUERIES
    # ═══════════════════════════════════════════════════════════════════

    def get_patient_directory_data(self):
        """All patients with joined last-visit, doctor, treatment, status."""
        query = """
            SELECT
                p.patient_id, p.patient_name, p.age, p.gender,
                p.contact, p.address, p.registration_date, p.medical_history,
                (SELECT MAX(a.appointment_date) FROM appointments a
                 WHERE a.patient_id = p.patient_id) AS last_visit,
                (SELECT s.staff_name FROM appointments a
                 JOIN staff s ON a.staff_id = s.staff_id
                 WHERE a.patient_id = p.patient_id
                 ORDER BY a.appointment_date DESC LIMIT 1) AS doctor_name,
                (SELECT tt.treatment_name FROM appointments a
                 JOIN treatment_types tt ON a.treatment_type_id = tt.treatment_type_id
                 WHERE a.patient_id = p.patient_id
                 ORDER BY a.appointment_date DESC LIMIT 1) AS treatment_name,
                (SELECT a.status FROM appointments a
                 WHERE a.patient_id = p.patient_id
                 ORDER BY a.appointment_date DESC LIMIT 1) AS appointment_status
            FROM patient p
            ORDER BY p.patient_name ASC
        """
        return self.execute_query(query) or []

    def get_patient_metrics(self):
        """KPIs for the Patients page top cards."""
        try:
            total_r = self.execute_query("SELECT COUNT(*) AS cnt FROM patient")
            total = total_r[0]['cnt'] if total_r else 0

            active_r = self.execute_query(
                "SELECT COUNT(DISTINCT patient_id) AS cnt FROM appointments "
                "WHERE appointment_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)")
            active = active_r[0]['cnt'] if active_r else 0

            weekly_r = self.execute_query(
                "SELECT COUNT(*) AS cnt FROM patient "
                "WHERE registration_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)")
            weekly = weekly_r[0]['cnt'] if weekly_r else 0

            growth = self.get_patient_growth_pct() if hasattr(self, 'get_patient_growth_pct') else 0
            if growth is None:
                growth = 0

            # Satisfaction heuristic from completed vs cancelled
            sat_r = self.execute_query(
                "SELECT "
                "COUNT(CASE WHEN status='completed' THEN 1 END) AS completed, "
                "COUNT(CASE WHEN status='cancelled' THEN 1 END) AS cancelled "
                "FROM appointments")
            comp = sat_r[0]['completed'] if sat_r else 0
            canc = sat_r[0]['cancelled'] if sat_r else 0
            if comp + canc > 0:
                satisfaction = round(3.0 + (comp / (comp + canc)) * 2.0, 1)
                satisfaction = min(satisfaction, 5.0)
            else:
                satisfaction = 0.0

            # Retention: patients with 2+ appointments
            ret_r = self.execute_query(
                "SELECT COUNT(*) AS cnt FROM ("
                "SELECT patient_id FROM appointments GROUP BY patient_id HAVING COUNT(*)>=2"
                ") sub")
            returning = ret_r[0]['cnt'] if ret_r else 0
            retention = round((returning / total) * 100, 1) if total > 0 else 0.0

            return {
                'satisfaction': satisfaction,
                'retention': retention,
                'active_records': active,
                'total_patients': total,
                'weekly_new': weekly,
                'growth_pct': growth,
            }
        except Exception as e:
            print(f"get_patient_metrics error: {e}")
            return {}

    def add_patient_directory(self, patient_name, age, gender, contact,
                              address, medical_history):
        """Insert patient with auto registration_date = CURDATE()."""
        query = """
            INSERT INTO patient
                (patient_name, age, gender, contact, address,
                 medical_history, registration_date)
            VALUES (%s, %s, %s, %s, %s, %s, CURDATE())
        """
        return self.execute_query(query,
            (patient_name, age, gender, contact, address, medical_history))

    def update_patient_directory(self, patient_id, patient_name, age,
                                 gender, contact, address, medical_history):
        query = """
            UPDATE patient
            SET patient_name=%s, age=%s, gender=%s,
                contact=%s, address=%s, medical_history=%s
            WHERE patient_id=%s
        """
        return self.execute_query(query,
            (patient_name, age, gender, contact, address,
             medical_history, patient_id))

    def get_filter_options(self):
        """Unique doctors and treatment types for filter dropdowns."""
        doctors = self.execute_query(
            "SELECT DISTINCT staff_id, staff_name FROM staff "
            "WHERE role='dentist' ORDER BY staff_name") or []
        treatments = self.execute_query(
            "SELECT treatment_type_id, treatment_name FROM treatment_types "
            "ORDER BY treatment_name") or []
        return {'doctors': doctors, 'treatments': treatments}

    def complete_appointment(self, appointment_id):
        query = "UPDATE appointments SET status = 'completed' WHERE appointment_id = %s"
        return self.execute_query(query, (appointment_id,))

    def cancel_appointment(self, appointment_id):
        query = "UPDATE appointments SET status = 'cancelled' WHERE appointment_id = %s"
        return self.execute_query(query, (appointment_id,))

    def get_treatment_types(self):
        query = "SELECT treatment_type_id, treatment_name, cost FROM treatment_types ORDER BY treatment_name"
        return self.execute_query(query) or []

    def get_all_bills(self):
        query = """
            SELECT b.bill_id, b.amount, b.status, b.payment_date, p.patient_name
            FROM billing b
            JOIN appointments a ON b.appointment_id = a.appointment_id
            JOIN patient p ON a.patient_id = p.patient_id
            ORDER BY b.bill_id DESC
        """
        return self.execute_query(query) or []

    def get_bills_by_status(self, status):
        query = """
            SELECT b.bill_id, b.amount, b.status, b.payment_date, p.patient_name
            FROM billing b
            JOIN appointments a ON b.appointment_id = a.appointment_id
            JOIN patient p ON a.patient_id = p.patient_id
            WHERE b.status = %s
            ORDER BY b.bill_id DESC
        """
        return self.execute_query(query, (status,)) or []

    def get_bill_details(self, bill_id):
        query = """
            SELECT b.*, p.patient_name, a.appointment_id
            FROM billing b
            JOIN appointments a ON b.appointment_id = a.appointment_id
            JOIN patient p ON a.patient_id = p.patient_id
            WHERE b.bill_id = %s
        """
        result = self.execute_query(query, (bill_id,))
        return result[0] if result else None

    def get_treatments_for_bill(self, bill_id):
        query = """
            SELECT tt.treatment_name, tt.cost
            FROM appointments a
            JOIN treatment_types tt ON a.treatment_type_id = tt.treatment_type_id
            JOIN billing b ON a.appointment_id = b.appointment_id
            WHERE b.bill_id = %s
        """
        return self.execute_query(query, (bill_id,)) or []

    def process_payment(self, bill_id):
        query = "UPDATE billing SET status = 'Paid' WHERE bill_id = %s"
        return self.execute_query(query, (bill_id,))

    def update_bill_status(self, bill_id, status):
        query = "UPDATE billing SET status = %s WHERE bill_id = %s"
        return self.execute_query(query, (status, bill_id))

    def void_bill(self, bill_id):
        query = "UPDATE billing SET status = 'Voided' WHERE bill_id = %s"
        return self.execute_query(query, (bill_id,))

    def get_all_inventory(self):
        query = "SELECT * FROM inventory ORDER BY item_name"
        return self.execute_query(query) or []

    def get_low_stock_items(self):
        query = "SELECT * FROM inventory WHERE quantity <= reorder_level ORDER BY quantity ASC"
        return self.execute_query(query) or []

    def get_inventory_item(self, item_id):
        query = "SELECT * FROM inventory WHERE item_id = %s"
        result = self.execute_query(query, (item_id,))
        return result[0] if result else None

    def update_inventory_item(self, item_id, item_name, quantity, price, reorder_level):
        query = """
            UPDATE inventory 
            SET item_name = %s, quantity = %s, price = %s, reorder_level = %s
            WHERE item_id = %s
        """
        return self.execute_query(query, (item_name, quantity, price, reorder_level, item_id))

    def restock_item(self, item_id, quantity):
        query = "CALL restock_item(%s, %s)"
        return self.execute_query(query, (item_id, quantity))

    def get_patient_summary(self, patient_id):
        query = """
            SELECT 
                COUNT(DISTINCT a.appointment_id) as total_visits,
                COALESCE(SUM(b.amount), 0) as total_spent
            FROM patient p
            LEFT JOIN appointments a ON p.patient_id = a.patient_id
            LEFT JOIN billing b ON a.appointment_id = b.appointment_id AND b.status = 'Paid'
            WHERE p.patient_id = %s
        """
        result = self.execute_query(query, (patient_id,))
        return result[0] if result else None

    # ═══════════════════════════════════════════════════════════════════
    # PROFILE & DASHBOARD QUERIES
    # ═══════════════════════════════════════════════════════════════════

    def get_logged_in_user_profile(self, user_id):
        """Full profile for the logged-in user, joining users + staff."""
        query = """
            SELECT u.user_id, u.username, u.email, u.role, u.phone,
                   s.staff_id, s.staff_name, s.profile_image
            FROM users u
            LEFT JOIN staff s ON u.user_id = s.user_id
            WHERE u.user_id = %s
        """
        result = self.execute_query(query, (user_id,))
        return result[0] if result else None

    def get_staff_profile_by_user(self, user_id):
        """Return staff row for a given user_id."""
        query = "SELECT * FROM staff WHERE user_id = %s"
        result = self.execute_query(query, (user_id,))
        return result[0] if result else None

    def update_staff_profile(self, user_id, staff_name, email, phone):
        """Update both staff and users tables in one call."""
        try:
            if not self.is_connected():
                self.connect()
            cursor = self.connection.cursor(dictionary=True)
            try:
                if not self.connection.in_transaction:
                    self.connection.start_transaction()
                # staff name
                cursor.execute(
                    "UPDATE staff SET staff_name = %s WHERE user_id = %s",
                    (staff_name, user_id))
                # user email + phone
                cursor.execute(
                    "UPDATE users SET email = %s, phone = %s WHERE user_id = %s",
                    (email, phone, user_id))
                self.connection.commit()
                return True
            except Exception as e:
                if self.connection.in_transaction:
                    self.connection.rollback()
                print(f"update_staff_profile error: {e}")
                return False
            finally:
                cursor.close()
        except Exception as e:
            print(f"update_staff_profile error: {e}")
            return False

    def update_profile_image(self, user_id, image_data):
        """Update profile_image in staff table.
        image_data can be a file-path string or BLOB bytes."""
        self.execute_query(
            "INSERT IGNORE INTO staff (user_id, staff_name, role) "
            "VALUES (%s, '', '')", (user_id,))
        query = "UPDATE staff SET profile_image = %s WHERE user_id = %s"
        return self.execute_query(query, (image_data, user_id))

    def get_treatment_type_split(self):
        """Appointment count grouped by treatment type → [{name, count, pct}]."""
        query = """
            SELECT tt.treatment_name, COUNT(a.appointment_id) AS count
            FROM appointments a
            JOIN treatment_types tt ON a.treatment_type_id = tt.treatment_type_id
            GROUP BY tt.treatment_name, tt.treatment_type_id
            ORDER BY count DESC
        """
        result = self.execute_query(query) or []
        total = sum(int(r['count']) for r in result)
        if total == 0:
            return []
        return [
            {'treatment_name': r['treatment_name'],
             'count': int(r['count']),
             'pct': round((int(r['count']) / total) * 100, 1)}
            for r in result
        ]

    def get_dashboard_stats(self):
        """One-call dashboard KPIs."""
        try:
            today_appts = self.get_today_appointments_count() or 0
            total_pts   = self.get_total_patients_count() or 0
            pending     = self.get_pending_bills_count() or 0
            low_stock   = self.get_low_stock_items_count() or 0
            pending_amt = 0
            try:
                r = self.execute_query(
                    "SELECT COALESCE(SUM(amount),0) AS t FROM billing WHERE status='Pending'")
                if r:
                    pending_amt = float(r[0]['t'])
            except Exception:
                pass
            growth = self.get_patient_growth_pct() or 0
            return {
                'today_appointments': today_appts,
                'total_patients': total_pts,
                'pending_bills': pending,
                'pending_amount': pending_amt,
                'low_stock': low_stock,
                'patient_growth': growth,
            }
        except Exception as e:
            print(f"get_dashboard_stats error: {e}")
            return {}

    def get_user_by_username(self, username):
        query = """
            SELECT u.user_id, u.username, u.email, u.role, s.staff_name
            FROM users u
            LEFT JOIN staff s ON u.user_id = s.user_id
            WHERE u.username = %s
        """
        result = self.execute_query(query, (username,))
        return result[0] if result else None

    def update_user_password_by_username(self, username, new_password):
        hashed_password = self.hash_password(new_password)
        query = """
            UPDATE users 
            SET password_hash = %s 
            WHERE username = %s
        """
        result = self.execute_query(query, (hashed_password, username))
        return result is not None and result != False

    def get_user_email(self, username):
        query = "SELECT email FROM users WHERE username = %s"
        result = self.execute_query(query, (username,))
        return result[0]['email'] if result and result[0].get('email') else None

    def get_user_phone(self, username):
        query = "SELECT phone FROM users WHERE username = %s"
        result = self.execute_query(query, (username,))
        return result[0]['phone'] if result and result[0].get('phone') else None

    def setup_recovery_columns(self):
        try:
            self.execute_query("ALTER TABLE users ADD COLUMN reset_code VARCHAR(10) NULL")
        except:
            pass
        try:
            self.execute_query("ALTER TABLE users ADD COLUMN reset_code_expiration DATETIME NULL")
        except:
            pass
        try:
            self.execute_query("ALTER TABLE users ADD COLUMN phone VARCHAR(20) NULL")
        except:
            pass

    def save_reset_code(self, username, code):
        self.setup_recovery_columns()
        query = """
            UPDATE users 
            SET reset_code = %s, reset_code_expiration = DATE_ADD(NOW(), INTERVAL 15 MINUTE)
            WHERE username = %s
        """
        return self.execute_query(query, (code, username))

    def validate_reset_code(self, username, code):
        query = """
            SELECT user_id FROM users 
            WHERE username = %s AND reset_code = %s AND reset_code_expiration > NOW()
        """
        result = self.execute_query(query, (username, code))
        return len(result) > 0 if result else False

    def clear_reset_code(self, username):
        query = """
            UPDATE users 
            SET reset_code = NULL, reset_code_expiration = NULL
            WHERE username = %s
        """
        return self.execute_query(query, (username,))

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate_user(self, username, password, role):
        hashed_password = self.hash_password(password)
        
        query = """
            SELECT u.user_id, u.username, u.role, s.staff_name
            FROM users u    
            LEFT JOIN staff s ON u.user_id = s.user_id
            WHERE u.username = %s AND u.password_hash = %s AND u.role = %s
        """
        result = self.execute_query(query, (username, hashed_password, role))
        return result[0] if result else None
    
    def get_user_by_email(self, email):
        query = """
            SELECT u.user_id, u.username, u.email, u.role, s.staff_name
            FROM users u
            LEFT JOIN staff s ON u.user_id = s.user_id
            WHERE u.email = %s
        """
        result = self.execute_query(query, (email,))
        return result[0] if result else None
    
    def email_exists(self, email):
        query = "SELECT COUNT(*) as count FROM users WHERE email = %s AND email IS NOT NULL"
        result = self.execute_query(query, (email,))
        return result[0]['count'] > 0 if result else False
    
    def update_user_password(self, email, new_password):
        hashed_password = self.hash_password(new_password)
        query = """
            UPDATE users 
            SET password_hash = %s 
            WHERE email = %s
        """
        result = self.execute_query(query, (hashed_password, email))
        return result is not None and result != False
    
    def is_first_time_login(self, user_id):
        query = "SELECT login_date FROM users WHERE user_id = %s"
        result = self.execute_query(query, (user_id,))
        
        if not result:
            return True
        
        login_date = result[0].get('login_date') if result else None
        return login_date is None
    
    def create_user(self, username, password, role, email, staff_name):
        hashed_password = self.hash_password(password)
        
        insert_user_query = """
            INSERT INTO users (username, password_hash, role, email, login_date)
            VALUES (%s, %s, %s, %s, NULL)
        """
        user_id = self.execute_query(insert_user_query, (username, hashed_password, role, email))
        
        if user_id:
            insert_staff_query = """
                INSERT INTO staff (user_id, staff_name, role)
                VALUES (%s, %s, %s)
            """
            self.execute_query(insert_staff_query, (user_id, staff_name, role))
            return user_id
        return None
    
    def check_username_exists(self, username):
        query = "SELECT user_id FROM users WHERE username = %s"
        result = self.execute_query(query, (username,))
        return len(result) > 0 if result else False
    
    # Views
    def get_appointment_report(self):
        query = "SELECT * FROM appointment_report ORDER BY appointment_date DESC"
        return self.execute_query(query) or []
    
    def get_billing_report(self):
        query = "SELECT * FROM billing_report ORDER BY payment_date DESC"
        return self.execute_query(query) or []
    
    def get_full_report(self):
        query = "SELECT * FROM full_report ORDER BY appointment_date DESC"
        return self.execute_query(query) or []
    
    def get_inventory_report(self):
        query = "SELECT * FROM inventory_report ORDER BY alert_status DESC, item_name"
        return self.execute_query(query) or []
    
    def get_patient_history(self, patient_name=None):
        if patient_name:
            query = "SELECT * FROM patient_history WHERE patient_name LIKE %s ORDER BY appointment_date DESC"
            return self.execute_query(query, (f'%{patient_name}%',)) or []
        else:
            query = "SELECT * FROM patient_history ORDER BY appointment_date DESC"
            return self.execute_query(query) or []
    
    def get_monthly_sales_report(self):
        query = "SELECT * FROM monthly_sales_report ORDER BY month DESC"
        return self.execute_query(query) or []
    
    def get_patient_treatment_count(self):
        query = "SELECT * FROM patient_treatment_count ORDER BY total_count DESC"
        return self.execute_query(query) or []
    
    def get_patients_with_pending_bills(self):
        query = """
            SELECT DISTINCT
                p.patient_id,
                p.patient_name,
                p.contact,
                (
                    SELECT COUNT(*) 
                    FROM billing b 
                    JOIN appointments a ON b.appointment_id = a.appointment_id
                    WHERE a.patient_id = p.patient_id 
                    AND b.status = 'Pending'
                ) as pending_bills_count,
                (
                    SELECT COALESCE(SUM(amount), 0)
                    FROM billing b 
                    JOIN appointments a ON b.appointment_id = a.appointment_id
                    WHERE a.patient_id = p.patient_id 
                    AND b.status = 'Pending'
                ) as total_pending_amount
            FROM patient p
            WHERE EXISTS (
                SELECT 1 
                FROM appointments a 
                JOIN billing b ON a.appointment_id = b.appointment_id
                WHERE a.patient_id = p.patient_id 
                AND b.status = 'Pending'
            )
            ORDER BY total_pending_amount DESC
        """
        return self.execute_query(query) or []
    
    def get_filtered_appointment_report(self, start_date=None, end_date=None, status=None):
        conditions = []
        params = []
        
        if start_date:
            conditions.append("appointment_date >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("appointment_date <= %s")
            params.append(end_date)
        if status:
            conditions.append("status = %s")
            params.append(status)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT * FROM appointment_report WHERE {where_clause} ORDER BY appointment_date DESC"
        return self.execute_query(query, tuple(params)) or []
    
    def get_filtered_billing_report(self, status=None, start_date=None, end_date=None):
        conditions = []
        params = []
        
        if status:
            conditions.append("status = %s")
            params.append(status)
        if start_date:
            conditions.append("payment_date >= %s")
            params.append(start_date)
        if end_date:
            conditions.append("payment_date <= %s")
            params.append(end_date)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT * FROM billing_report WHERE {where_clause} ORDER BY payment_date DESC"
        return self.execute_query(query, tuple(params)) or []

    def reset_appointment_auto_increment(self):
        try:
            count_query = "SELECT COUNT(*) as count FROM appointments"
            result = self.execute_query(count_query)
            if result and result[0]['count'] == 0:
                reset_query = "ALTER TABLE appointments AUTO_INCREMENT = 1"
                self.execute_query(reset_query)
                print("Appointments table AUTO_INCREMENT reset to 1")
                return True
            else:
                print(f"Appointments table has {result[0]['count'] if result else 0} rows. AUTO_INCREMENT not reset.")
                return False
        except Exception as e:
            print(f"Error resetting AUTO_INCREMENT: {e}")
            return False
    
    def create_single_treatment_appointment(self, patient_id, appointment_date, treatment_name, cost=0, staff_id=None, status='scheduled'):
        try:
            if not self.is_connected():
                self.connect()
            
            cursor = self.connection.cursor(dictionary=True)
            
            try:
                if not self.connection.in_transaction:
                    self.connection.start_transaction()
                
                if staff_id is None:
                    cursor.execute("SELECT staff_id FROM staff WHERE role = 'dentist' LIMIT 1")
                    staff_result = cursor.fetchone()
                    staff_id = staff_result['staff_id'] if staff_result else None
                
                cursor.execute("SELECT treatment_type_id, cost FROM treatment_types WHERE treatment_name = %s", (treatment_name,))
                existing = cursor.fetchone()
                
                if existing:
                    treatment_type_id = existing['treatment_type_id']
                    if cost == 0:
                        cost = existing.get('cost', 0)
                else:
                    cursor.execute("INSERT INTO treatment_types (treatment_name, cost) VALUES (%s, %s)", 
                                  (treatment_name, cost))
                    treatment_type_id = cursor.lastrowid
                
                query_appointment = """
                    INSERT INTO appointments (patient_id, appointment_date, status, staff_id, treatment_type_id)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(query_appointment, (patient_id, appointment_date, status, staff_id, treatment_type_id))
                appointment_id = cursor.lastrowid
                
                if not appointment_id:
                    raise Exception("Failed to create appointment")
                
                query_billing = """
                    INSERT INTO billing (appointment_id, amount, status, payment_date)
                    VALUES (%s, %s, 'Pending', NULL)
                """
                cursor.execute(query_billing, (appointment_id, cost))
                
                self.connection.commit()
                print(f"Appointment created successfully! ID: {appointment_id}")
                return appointment_id
                
            except Exception as e:
                if self.connection.in_transaction:
                    self.connection.rollback()
                print(f"Transaction error: {e}")
                return None
            finally:
                cursor.close()
                
        except Exception as e:
            print(f"Error in create_single_treatment_appointment: {e}")
            return None

    def delete_appointment(self, appointment_id):
        try:
            query_billing = "DELETE FROM billing WHERE appointment_id = %s"
            self.execute_query(query_billing, (appointment_id,))
            
            query = "DELETE FROM appointments WHERE appointment_id = %s"
            result = self.execute_query(query, (appointment_id,))
            
            if result:
                print(f"Appointment {appointment_id} and its child records deleted successfully")
            
            return True if result is not None else False
        except Exception as e:
            print(f"Error deleting appointment: {e}")
            return False

    def get_all_appointments_with_details(self):
        query = """
            SELECT 
                a.appointment_id,
                a.appointment_date,
                a.status,
                p.patient_name,
                p.age,
                p.gender,
                s.staff_name as doctor_name,
                tt.treatment_name
            FROM appointments a
            JOIN patient p ON a.patient_id = p.patient_id
            LEFT JOIN staff s ON s.staff_id = a.staff_id
            LEFT JOIN treatment_types tt ON a.treatment_type_id = tt.treatment_type_id
            ORDER BY a.appointment_date DESC
        """
        return self.execute_query(query) or []

    def get_all_doctors(self):
        query = "SELECT staff_id, staff_name FROM staff WHERE role = 'dentist'"
        return self.execute_query(query) or []

    def get_all_treatments_list(self):
        query = "SELECT treatment_type_id, treatment_name, cost FROM treatment_types ORDER BY treatment_name"
        return self.execute_query(query) or []

    def search_appointments(self, search_term):
        query = """
            SELECT 
                a.appointment_id,
                a.appointment_date,
                a.status,
                p.patient_name,
                s.staff_name as doctor_name,
                tt.treatment_name
            FROM appointments a
            JOIN patient p ON a.patient_id = p.patient_id
            LEFT JOIN staff s ON s.role = 'dentist'
            LEFT JOIN treatment_types tt ON a.treatment_type_id = tt.treatment_type_id
            WHERE p.patient_name LIKE %s 
            OR tt.treatment_name LIKE %s
            OR a.status LIKE %s
            ORDER BY a.appointment_date DESC
        """
        search_pattern = f"%{search_term}%"
        return self.execute_query(query, (search_pattern, search_pattern, search_pattern)) or []

    def get_all_patients_with_stats(self):
        query = """
            SELECT 
                p.patient_id,
                p.patient_name,
                p.contact,
                p.registration_date,
                MAX(a.appointment_date) as last_visit,
                COUNT(a.appointment_id) as total_visits
            FROM patient p
            LEFT JOIN appointments a ON p.patient_id = a.patient_id
            GROUP BY p.patient_id, p.patient_name, p.contact, p.registration_date
            ORDER BY p.registration_date DESC
        """
        return self.execute_query(query) or []

    def add_patient(self, name, contact, email, address, medical_history, dob):
        query = """
            INSERT INTO patient (patient_name, contact, email, address, medical_history, date_of_birth, registration_date)
            VALUES (%s, %s, %s, %s, %s, %s, CURDATE())
        """
        return self.execute_query(query, (name, contact, email, address, medical_history, dob))

    def update_patient_full(self, patient_id, name, contact, email, address, medical_history, dob):
        query = """
            UPDATE patient 
            SET patient_name = %s, contact = %s, email = %s, 
                address = %s, medical_history = %s, date_of_birth = %s
            WHERE patient_id = %s
        """
        return self.execute_query(query, (name, contact, email, address, medical_history, dob, patient_id))
    
    def get_today_appointments_count(self):
        query = "SELECT COUNT(*) as count FROM appointments WHERE DATE(appointment_date) = CURDATE()"
        result = self.execute_query(query)
        return result[0]['count'] if result else 0
    
    def get_total_patients_count(self):
        query = "SELECT COUNT(*) as count FROM patient"
        result = self.execute_query(query)
        return result[0]['count'] if result else 0
    
    def get_upcoming_appointments(self, limit=5):
        query = """
            SELECT a.appointment_id, a.appointment_date, p.patient_name, 
                   a.status, s.staff_name as doctor_name, tt.treatment_name
            FROM appointments a
            JOIN patient p ON a.patient_id = p.patient_id
            JOIN staff s ON a.staff_id = s.staff_id
            LEFT JOIN treatment_types tt ON a.treatment_type_id = tt.treatment_type_id
            WHERE a.appointment_date >= NOW()
            ORDER BY a.appointment_date ASC
            LIMIT %s
        """
        return self.execute_query(query, (limit,)) or []
    
    def get_pending_bills_count(self):
        query = "SELECT COUNT(*) as count FROM billing WHERE status = 'Pending'"
        result = self.execute_query(query)
        return result[0]['count'] if result else 0
    
    def get_low_stock_items_count(self):
        query = "SELECT COUNT(*) as count FROM inventory WHERE quantity <= reorder_level"
        result = self.execute_query(query)
        return result[0]['count'] if result else 0
    
    def get_monthly_sales(self):
        query = """
            SELECT DATE_FORMAT(payment_date, '%Y-%m') as month, SUM(amount) as total
            FROM billing
            WHERE status = 'Paid' AND payment_date IS NOT NULL
            GROUP BY DATE_FORMAT(payment_date, '%Y-%m')
            ORDER BY month DESC
            LIMIT 6
        """
        return self.execute_query(query) or []
    
    def get_patients_per_day(self):
        query = """
            SELECT DAYNAME(appointment_date) as day, COUNT(*) as count
            FROM appointments
            WHERE appointment_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY DAYNAME(appointment_date)
            ORDER BY FIELD(DAYNAME(appointment_date), 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
        """
        return self.execute_query(query) or []
    
    def setup_recovery_columns(self):
        """Ensure recovery columns exist in users table"""
        try:
            # Check if columns exist and add if missing
            check_query = """
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'users' 
                AND COLUMN_NAME = %s
            """
            
            columns_to_add = [
                ('phone', 'VARCHAR(20) NULL'),
                ('reset_code', 'VARCHAR(10) NULL'),
                ('reset_code_expiration', 'DATETIME NULL')
            ]
            
            for col_name, col_definition in columns_to_add:
                result = self.execute_query(check_query, (col_name,))
                if not result:
                    try:
                        alter_query = f"ALTER TABLE users ADD COLUMN {col_name} {col_definition}"
                        self.execute_query(alter_query)
                        print(f"Added column: {col_name}")
                    except Exception as e:
                        print(f"Column {col_name} may already exist: {e}")
                        
        except Exception as e:
            print(f"Error setting up recovery columns: {e}")

    def generate_and_save_reset_code(self, username):
        """Generate a 6-digit code and save it to database"""
        import random
        code = f"{random.randint(100000, 999999)}"
        
        query = """
            UPDATE users 
            SET reset_code = %s, 
                reset_code_expiration = DATE_ADD(NOW(), INTERVAL 15 MINUTE)
            WHERE username = %s
        """
        
        result = self.execute_query(query, (code, username))
        return code if result else None

    def validate_reset_code(self, username, code):
        """Validate reset code and check expiration"""
        query = """
            SELECT user_id 
            FROM users 
            WHERE username = %s 
            AND reset_code = %s 
            AND reset_code_expiration > NOW()
        """
        
        result = self.execute_query(query, (username, code))
        return len(result) > 0 if result else False

    def clear_reset_code(self, username):
        """Clear reset code after successful password reset"""
        query = """
            UPDATE users 
            SET reset_code = NULL, 
                reset_code_expiration = NULL
            WHERE username = %s
        """
        return self.execute_query(query, (username,))

    def is_reset_code_valid(self, username):
        """Check if user has a valid (non-expired) reset code"""
        query = """
            SELECT 1
            FROM users 
            WHERE username = %s 
            AND reset_code IS NOT NULL 
            AND reset_code_expiration > NOW()
        """
        result = self.execute_query(query, (username,))
        return len(result) > 0 if result else False
    
    def send_recovery_email(self, to_email, username, code):
        """Send OTP recovery email using SMTP"""
        try:
            from dashboard_gui.style import Config
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            smtp_host = getattr(Config, 'SMTP_HOST', None)
            smtp_port = getattr(Config, 'SMTP_PORT', None)
            smtp_email = getattr(Config, 'SMTP_EMAIL', None)
            smtp_password = getattr(Config, 'SMTP_PASSWORD', None)
            smtp_from_name = getattr(Config, 'SMTP_FROM_NAME', 'LC Dental Care')
            smtp_use_tls = getattr(Config, 'SMTP_USE_TLS', True)

            if not all([smtp_host, smtp_port, smtp_email, smtp_password]):
                print("Error: SMTP configuration is incomplete in Config class.")
                print("Please add SMTP_HOST, SMTP_PORT, SMTP_EMAIL, SMTP_PASSWORD to Config.")
                return False

            if smtp_password == "your_app_password_here":
                print("Error: SMTP_PASSWORD is still set to the default placeholder.")
                print("Please replace it with your actual app password in style.py Config.")
                return False

            subject = "LC Dental Care - Password Recovery Code"

            html_body = f"""
            <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 500px; margin: 0 auto; background: #f8fafc; border-radius: 16px; overflow: hidden;">
                <div style="background: #1E3A8A; padding: 30px 20px; text-align: center;">
                    <h1 style="color: white; margin: 0; font-size: 22px; font-weight: 700;">LC Dental Care</h1>
                    <p style="color: #93c5fd; margin: 5px 0 0 0; font-size: 13px;">Password Recovery</p>
                </div>
                <div style="padding: 30px 25px; background: white;">
                    <p style="color: #334155; font-size: 15px; line-height: 1.6; margin: 0 0 20px 0;">
                        Hello <strong>{username}</strong>,
                    </p>
                    <p style="color: #475569; font-size: 14px; line-height: 1.6; margin: 0 0 25px 0;">
                        We received a request to reset your password. Use the verification code below to proceed:
                    </p>
                    <div style="background: #f1f5f9; border: 2px dashed #cbd5e1; border-radius: 12px; padding: 20px; text-align: center; margin: 0 0 25px 0;">
                        <span style="font-size: 36px; font-weight: 800; color: #1E3A8A; letter-spacing: 8px;">{code}</span>
                    </div>
                    <p style="color: #94a3b8; font-size: 12px; margin: 0 0 20px 0; text-align: center;">
                        This code expires in <strong>15 minutes</strong>. Do not share this code with anyone.
                    </p>
                    <div style="border-top: 1px solid #e2e8f0; padding-top: 20px; margin-top: 20px;">
                        <p style="color: #94a3b8; font-size: 12px; line-height: 1.5; margin: 0;">
                            If you did not request this password reset, please ignore this email or contact our clinic immediately.
                        </p>
                    </div>
                </div>
                <div style="background: #f8fafc; padding: 15px 25px; text-align: center; border-top: 1px solid #e2e8f0;">
                    <p style="color: #94a3b8; font-size: 11px; margin: 0;">LC Dental Care - Clinical Management System</p>
                </div>
            </div>
            """

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{smtp_from_name} <{smtp_email}>"
            msg["To"] = to_email
            msg.attach(MIMEText(html_body, "html"))

            server = smtplib.SMTP(smtp_host, int(smtp_port))
            if smtp_use_tls:
                server.starttls()
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, to_email, msg.as_string())
            server.quit()

            return True

        except ImportError:
            print("Error: Could not import Config from style.py")
            return False
        except smtplib.SMTPAuthenticationError:
            print("Error: SMTP authentication failed. Check SMTP_EMAIL and SMTP_PASSWORD.")
            return False
        except smtplib.SMTPConnectError:
            print("Error: Could not connect to SMTP server. Check SMTP_HOST and SMTP_PORT.")
            return False
        except Exception as e:
            print(f"Error sending recovery email: {e}")
            return False
        
    def get_full_profile(self, user_id):
        query = """
            SELECT u.user_id, u.username, u.email, u.role, u.phone,
                   s.staff_name, s.profile_image
            FROM users u
            LEFT JOIN staff s ON u.user_id = s.user_id
            WHERE u.user_id = %s
        """
        result = self.execute_query(query, (user_id,))
        return result[0] if result else None

    def update_user_profile_info(self, user_id, email, phone):
        query = "UPDATE users SET email = %s, phone = %s WHERE user_id = %s"
        return self.execute_query(query, (email, phone, user_id))

    def update_user_profile_image(self, user_id, image_path):
        # Ensure staff row exists for this user
        self.execute_query("INSERT IGNORE INTO staff (user_id) VALUES (%s)", (user_id,))
        query = "UPDATE staff SET profile_image = %s WHERE user_id = %s"
        return self.execute_query(query, (image_path, user_id))

    def get_appointment_split(self):
        query = "SELECT status, COUNT(*) as count FROM appointments GROUP BY status"
        result = self.execute_query(query) or []
        total = sum(r['count'] for r in result)
        if total == 0: return []
        return [{'status': r['status'], 'count': r['count'], 'pct': round((r['count']/total)*100)} for r in result]

    def get_patient_growth_pct(self):
        try:
            query = """
                SELECT 
                    (SELECT COUNT(*) FROM patient WHERE registration_date >= DATE_SUB(CURDATE(), INTERVAL 1 MONTH)) as this_month,
                    (SELECT COUNT(*) FROM patient WHERE registration_date >= DATE_SUB(CURDATE(), INTERVAL 2 MONTH) AND registration_date < DATE_SUB(CURDATE(), INTERVAL 1 MONTH)) as last_month
            """
            result = self.execute_query(query)
            if result and result[0]['last_month'] > 0:
                return int(((result[0]['this_month'] - result[0]['last_month']) / result[0]['last_month']) * 100)
            elif result and result[0]['this_month'] > 0: return 100
            return 0
        except: return 0

    def update_user_password_secure(self, user_id, old_password, new_password):
        old_hash = self.hash_password(old_password)
        new_hash = self.hash_password(new_password)
        query = """
            SELECT user_id FROM users 
            WHERE user_id = %s AND password_hash = %s
        """
        result = self.execute_query(query, (user_id, old_hash))
        if not result:
            return False
        update = "UPDATE users SET password_hash = %s WHERE user_id = %s"
        return self.execute_query(update, (new_hash, user_id))

    def get_revenue_trends(self, days=7):
        if days == 1:
            query = """
                SELECT HOUR(payment_date) as hour, COALESCE(SUM(amount), 0) as revenue
                FROM billing
                WHERE status = 'Paid' AND DATE(payment_date) = CURDATE()
                GROUP BY HOUR(payment_date)
                ORDER BY hour ASC
            """
            result = self.execute_query(query) or []
            from datetime import datetime
            trends, labels = [], []
            for h in range(8, 18):
                hr_rev = next((float(r['revenue']) for r in result if r['hour'] == h), 0.0)
                trends.append(hr_rev)
                labels.append(f"{h % 12 or 12}{'am' if h < 12 else 'pm'}")
            return trends, labels
        elif days <= 31:
            query = """
                SELECT DATE_FORMAT(payment_date, '%%Y-%%m-%%d') as date,
                       COALESCE(SUM(amount), 0) as revenue
                FROM billing
                WHERE status = 'Paid' AND payment_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                GROUP BY DATE_FORMAT(payment_date, '%%Y-%%m-%%d')
                ORDER BY date ASC
            """
            result = self.execute_query(query, (days,)) or []
            from datetime import datetime, timedelta
            trends, labels = [], []
            for i in range(days):
                date = (datetime.now() - timedelta(days=days-1-i)).strftime('%Y-%m-%d')
                day_rev = next((float(r['revenue']) for r in result if r['date'] == date), 0.0)
                trends.append(day_rev)
                labels.append(datetime.strptime(date, '%Y-%m-%d').strftime('%d'))
            return trends, labels
        else:
            query = """
                SELECT DATE_FORMAT(payment_date, '%%Y-%%m') as month,
                       COALESCE(SUM(amount), 0) as total
                FROM billing
                WHERE status = 'Paid' AND payment_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
                GROUP BY DATE_FORMAT(payment_date, '%%Y-%%m')
                ORDER BY month ASC
            """
            result = self.execute_query(query) or []
            from datetime import datetime, timedelta
            trends, labels = [], []
            for i in range(12):
                date = (datetime.now() - timedelta(days=365-1-i)).strftime('%Y-%m')
                month_rev = next((float(r['total']) for r in result if r['month'] == date), 0.0)
                trends.append(month_rev)
                labels.append(datetime.strptime(date, '%Y-%m').strftime('%b'))
            return trends, labels

    def get_appointment_volume(self, days=7):
        if days == 1:
            query = """
                SELECT HOUR(appointment_date) as hour, COUNT(*) as count
                FROM appointments
                WHERE DATE(appointment_date) = CURDATE()
                GROUP BY HOUR(appointment_date)
                ORDER BY hour ASC
            """
            result = self.execute_query(query) or []
            volumes = []
            for h in range(8, 18):
                hr_cnt = next((int(r['count']) for r in result if r['hour'] == h), 0)
                volumes.append(hr_cnt)
            return volumes
        elif days <= 31:
            query = """
                SELECT DATE_FORMAT(appointment_date, '%%Y-%%m-%%d') as date, COUNT(*) as count
                FROM appointments
                WHERE appointment_date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
                GROUP BY DATE_FORMAT(appointment_date, '%%Y-%%m-%%d')
                ORDER BY date ASC
            """
            result = self.execute_query(query, (days,)) or []
            from datetime import datetime, timedelta
            volumes = []
            for i in range(days):
                date = (datetime.now() - timedelta(days=days-1-i)).strftime('%Y-%m-%d')
                day_cnt = next((int(r['count']) for r in result if r['date'] == date), 0)
                volumes.append(day_cnt)
            return volumes
        else:
            query = """
                SELECT DATE_FORMAT(appointment_date, '%%Y-%%m') as month, COUNT(*) as count
                FROM appointments
                WHERE appointment_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
                GROUP BY DATE_FORMAT(appointment_date, '%%Y-%%m')
                ORDER BY month ASC
            """
            result = self.execute_query(query) or []
            from datetime import datetime, timedelta
            volumes = []
            for i in range(12):
                date = (datetime.now() - timedelta(days=365-1-i)).strftime('%Y-%m')
                month_cnt = next((int(r['count']) for r in result if r['month'] == date), 0)
                volumes.append(month_cnt)
            return volumes

    # ──────────────────────────────────────────────────────────
    # Weekday-based trends (for "Month" chart filter: Mon–Sun)
    # ──────────────────────────────────────────────────────────
    def get_revenue_weekday_trends(self):
        """Revenue grouped by day-of-week for the last 30 days → (values, labels)."""
        query = """
            SELECT DAYNAME(payment_date) AS day,
                   COALESCE(SUM(amount), 0) AS revenue
            FROM billing
            WHERE status = 'Paid'
              AND payment_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            GROUP BY DAYNAME(payment_date)
            ORDER BY FIELD(DAYNAME(payment_date),
                           'Monday','Tuesday','Wednesday',
                           'Thursday','Friday','Saturday','Sunday')
        """
        result = self.execute_query(query) or []
        day_index = {
            'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3,
            'Friday': 4, 'Saturday': 5, 'Sunday': 6,
        }
        revenues = [0.0] * 7
        labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for r in result:
            d = r.get('day', '')
            if d in day_index:
                revenues[day_index[d]] = float(r['revenue'])
        return revenues, labels

    def get_appointment_weekday_volume(self):
        """Appointment count by day-of-week for the last 30 days → (values, labels)."""
        query = """
            SELECT DAYNAME(appointment_date) AS day, COUNT(*) AS count
            FROM appointments
            WHERE appointment_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            GROUP BY DAYNAME(appointment_date)
            ORDER BY FIELD(DAYNAME(appointment_date),
                           'Monday','Tuesday','Wednesday',
                           'Thursday','Friday','Saturday','Sunday')
        """
        result = self.execute_query(query) or []
        day_index = {
            'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3,
            'Friday': 4, 'Saturday': 5, 'Sunday': 6,
        }
        volumes = [0] * 7
        labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for r in result:
            d = r.get('day', '')
            if d in day_index:
                volumes[day_index[d]] = int(r['count'])
        return volumes, labels

    def get_monthly_sales(self):
        """Get monthly revenue for the past 12 months"""
        query = """
            SELECT DATE_FORMAT(payment_date, '%Y-%m') as month, 
                   SUM(amount) as total
            FROM billing
            WHERE status = 'Paid' AND payment_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
            GROUP BY DATE_FORMAT(payment_date, '%Y-%m')
            ORDER BY month ASC
        """
        result = self.execute_query(query)
        if not result: return [], []
        from datetime import datetime, timedelta    # <-- ADD timedelta HERE
        trends, labels = [], []
        for i in range(12):
            date = (datetime.now() - timedelta(days=365-1-i)).strftime('%Y-%m')
            month_rev = next((float(r['total']) for r in result if r['month'] == date), 0.0)
            trends.append(month_rev)
            labels.append(datetime.strptime(date, '%Y-%m').strftime('%b'))
        return trends, labels
    
    def get_appointment_split(self):
        """Get appointment distribution by treatment type"""
        query = """
            SELECT 
                COALESCE(tt.treatment_name, 'Other') as treatment,
                COUNT(*) as count
            FROM appointments a
            LEFT JOIN treatment_types tt ON a.treatment_type_id = tt.treatment_type_id
            WHERE a.appointment_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY tt.treatment_name
            ORDER BY count DESC
            LIMIT 5
        """
        return self.execute_query(query) or []
    
    def get_patient_growth(self):
        """Calculate patient growth percentage from last month"""
        query = """
            SELECT 
                (SELECT COUNT(*) FROM patient WHERE DATE(registration_date) >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)) as new_patients,
                (SELECT COUNT(*) FROM patient WHERE DATE(registration_date) < DATE_SUB(CURDATE(), INTERVAL 30 DAY)) as existing_patients
        """
        result = self.execute_query(query)
        if result and result[0]['existing_patients'] > 0:
            growth = (result[0]['new_patients'] / result[0]['existing_patients']) * 100
            return round(growth, 1)
        return 0.0
    
    def get_pending_bills_total(self):
        """Get total amount of pending bills"""
        query = "SELECT COALESCE(SUM(amount), 0) as total FROM billing WHERE status = 'Pending'"
        result = self.execute_query(query)
        return float(result[0]['total']) if result else 0.0
    
    def search_all(self, search_term):
        """Search across patients, appointments, and inventory"""
        search_pattern = f"%{search_term}%"
        results = {
            'patients': [],
            'appointments': [],
            'inventory': []
        }
        
        # Search patients
        patient_query = """
            SELECT patient_id, patient_name, contact, email 
            FROM patient 
            WHERE patient_name LIKE %s OR contact LIKE %s OR email LIKE %s
            LIMIT 10
        """
        results['patients'] = self.execute_query(patient_query, (search_pattern, search_pattern, search_pattern)) or []
        
        # Search appointments
        appointment_query = """
            SELECT a.appointment_id, a.appointment_date, a.status, p.patient_name, tt.treatment_name
            FROM appointments a
            JOIN patient p ON a.patient_id = p.patient_id
            LEFT JOIN treatment_types tt ON a.treatment_type_id = tt.treatment_type_id
            WHERE p.patient_name LIKE %s OR tt.treatment_name LIKE %s
            LIMIT 10
        """
        results['appointments'] = self.execute_query(appointment_query, (search_pattern, search_pattern)) or []
        
        # Search inventory
        inventory_query = """
            SELECT item_id, item_name, quantity, price
            FROM inventory
            WHERE item_name LIKE %s
            LIMIT 10
        """
        results['inventory'] = self.execute_query(inventory_query, (search_pattern,)) or []
        
        return results
    
    def get_user_profile(self, user_id):
        """Get user profile information"""
        query = """
            SELECT u.user_id, u.username, u.email, u.role, s.staff_name, s.profile_image
            FROM users u
            LEFT JOIN staff s ON u.user_id = s.user_id
            WHERE u.user_id = %s
        """
        result = self.execute_query(query, (user_id,))
        return result[0] if result else None
    
    def update_user_profile_image(self, user_id, image_path):
        """Update user's profile image path"""
        query = """
            UPDATE staff 
            SET profile_image = %s 
            WHERE user_id = %s
        """
        return self.execute_query(query, (image_path, user_id))
    
    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()