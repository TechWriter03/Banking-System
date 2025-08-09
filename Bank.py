import mysql.connector
import random
from datetime import date
import csv

class Person:
    def __init__(self,name):
        self.name=name

class Customer(Person):
    def __init__(self,name,initial_deposit,atm_pin):
        super().__init__(name)
        self.__balance=initial_deposit
        self.__account_number=random.randint(10000,99999)
        self.__atm_pin=atm_pin

    def get_account_number(self):
        return self.__account_number

    def get_balance(self):
        return self.__balance
    
    def get_atm_pin(self):
        return self.__atm_pin

class Bank:
    def __init__(self):
        self.conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="bank"
        )
        if self.conn.is_connected():
            print("Connected to MySQL Database...")
        self.cursor=self.conn.cursor()

    def create_account(self):
        name=input("Enter customer name: ")
        initial_deposit=float(input("Enter amount to deposit: "))
        atm_pin=input("Enter 4 Digit ATM PIN: ")
        if len(atm_pin)!=4:
            print("Please enter 4 digit pin.")
            print("Account not created. Try again !")
            return
        customer=Customer(name,initial_deposit,atm_pin)
        query="INSERT INTO accounts (name,account_number,balance,atm_pin) VALUES (%s,%s,%s,%s)"
        values=(customer.name,customer.get_account_number(),customer.get_balance(),customer.get_atm_pin())
        self.cursor.execute(query,values)
        self.conn.commit()
        print("Account created successfully. Account Number:",customer.get_account_number())

    def access_account(self):
        name=input("Enter customer name: ")
        account_number=input("Enter account number: ")
        query="SELECT name,account_number FROM accounts WHERE name=%s AND account_number=%s"
        values=(name,account_number)
        self.cursor.execute(query,values)
        result=self.cursor.fetchone()
        if result:
            while True:
                print("Welcome ",result[0])
                print("Your account number is ",result[1])
                print("1. Deposit")
                print("2. Withdraw")
                print("3. Check Balance")
                print("4. Close Account")
                print("5. Logout")
                choice=int(input("Enter your choice: "))
                if choice==1:
                    amount=float(input("Enter amount to deposit: "))
                    self.deposit(True,result[1],amount)
                elif choice==2:
                    amount=float(input("Enter amount to withdraw: "))
                    self.withdraw(True,result[1],amount)
                elif choice==3:
                    self.check_balance(False,result[1])
                elif choice==4:
                    self.close_account(result[1])
                elif choice==5:
                    print("Logged Out successfully...")
                else:
                    print("Invalid Choice...")
                    break
        else:
            print("Account not found. Please enter correct details")

    def deposit(self,flag,account_number,amount):
        old_balance=self.check_balance(True,account_number)
        new_balance=float(old_balance)+amount
        self.update_balance(new_balance,account_number)
        if flag:
            query="INSERT INTO transactions (from_account,to_account,amount) VALUES (%s,%s,%s)"
            values=("self",account_number,amount)
            self.cursor.execute(query,values)
            self.conn.commit()

    def withdraw(self,flag,account_number,amount):
        old_balance=self.check_balance(True,account_number)
        if amount<old_balance:
            new_balance=float(old_balance)-amount
            self.update_balance(new_balance,account_number)
            if flag:
                query="INSERT INTO transactions (from_account,to_account,amount) VALUES (%s,%s,%s)"
                values=(account_number,"self",amount)
                self.cursor.execute(query,values)
                self.conn.commit()
        else:
            print("Insufficient Balance...")

    def check_balance(self,flag,account_number):
        query="SELECT balance FROM accounts WHERE account_number=%s"
        self.cursor.execute(query,(account_number,))
        result=self.cursor.fetchone()
        if flag:
            return result[0]
        else:
            print("Account Number: ",account_number)
            print("Available Balance: ",result[0])

    def update_balance(self,new_balance,account_number):
        query="UPDATE accounts SET balance=%s WHERE account_number=%s"
        values=(new_balance,account_number)
        self.cursor.execute(query,values)
        self.conn.commit()
        self.check_balance(False,account_number)

    def close_account(self,account_number):
        choice=input("Are you sure to close account(yes/no): ")
        if choice=="yes":
            query="DELETE FROM accounts WHERE account_number=%s"
            self.cursor.execute(query,(account_number,))
            self.conn.commit()
            print("Account closed successfully...")
        else:
            print("Account not closed...")

    def transfer_funds(self):
        from_account=input("Enter account number (FROM): ")
        to_account=input("Enter account number (TO): ")
        amount=float(input("Enter amount to transfer: "))
        if self.check_account(from_account) and self.check_account(to_account):
            from_balance=self.check_balance(True,from_account)
            if amount<from_balance:
                self.withdraw(False,from_account,amount)
                self.deposit(False,to_account,amount)
                query="INSERT INTO transactions (from_account,to_account,amount) VALUES (%s,%s,%s)"
                values=(from_account,to_account,amount)
                self.cursor.execute(query,values)
                self.conn.commit()
                print("Funds transferred successfully and transaction recorded...")
            else:
                print("Insufficient balance for transfer...")
        else:
            print("Account not found...")

    def check_account(self,account_number):
        query="SELECT * FROM accounts WHERE account_number=%s"
        self.cursor.execute(query,(account_number,))
        result=self.cursor.fetchone()
        if result:
            return True
        else:
            return False
        
    def create_fixed_deposit(self):
        account_number = input("Enter your account number: ")
        if not self.check_account(account_number):
            print("Account not found.")
            return
        deposit_amount = float(input("Enter deposit amount: "))
        tenure = int(input("Enter tenure in years: "))
        interest_rate = float(input("Enter interest rate (%): "))
        start_date = date.today()
        maturity_date = date(start_date.year + tenure, start_date.month, start_date.day)
        maturity_amount = round(deposit_amount * ((1 + (interest_rate / 100)) ** tenure), 2)
        query = '''INSERT INTO fixed_deposits 
                (account_number, deposit_amount, interest_rate, tenure, 
                 start_date, maturity_date, maturity_amount)
                VALUES (%s, %s, %s, %s, %s, %s, %s)'''
        values = (account_number, deposit_amount, interest_rate, tenure,
                  start_date, maturity_date, maturity_amount)
        self.cursor.execute(query, values)
        self.conn.commit()
        print("Fixed Deposit created successfully...")
        self.get_fd_details(account_number)

    def get_fd_details(self,account_number):
        query = '''SELECT deposit_amount, interest_rate, tenure, maturity_date, maturity_amount
                FROM fixed_deposits WHERE account_number=%s'''
        self.cursor.execute(query, (account_number,))
        result = self.cursor.fetchall()
        for fd in result:
            print("\n--- Fixed Deposit Details ---")
            print("Deposit Amount      :", fd[0])
            print("Interest Rate       :", fd[1], "%")
            print("Tenure              :", fd[2], "years")
            print("Maturity Date       :", fd[3])
            print("Maturity Amount     :", fd[4])

    def apply_interest(self):
        interest=float(input("Enter interest rate (%): "))
        interest/=100
        query="SELECT account_number,balance FROM accounts"
        self.cursor.execute(query)
        accounts=self.cursor.fetchall()
        for acc in accounts:
            account_number=acc[0]
            old_balance=acc[1]
            old_balance=float(old_balance)
            interest_amount=old_balance*interest
            new_balance=old_balance+interest_amount
            query="UPDATE accounts SET balance=%s WHERE account_number=%s"
            self.cursor.execute(query,(new_balance,account_number))
            query="INSERT INTO transactions (from_account,to_account,amount) VALUES (%s,%s,%s)"
            values=("bank",account_number,interest_amount)
            self.cursor.execute(query,values)
        self.conn.commit()
        print("Interest applied to all accounts...")

    def change_atm_pin(self):
        account_number=input("Enter account number: ")
        if self.check_account(account_number):
            old_pin=input("Enter old ATM PIN: ")
            query="SELECT atm_pin FROM accounts WHERE account_number=%s"
            self.cursor.execute(query,(account_number,))
            result=self.cursor.fetchone()
            if result and old_pin==result[0]:
                new_pin=input("Enter new ATM PIN: ")
                if not new_pin.isdigit() or len(new_pin) != 4:
                    print("Please enter a valid 4-digit PIN.")
                    print("PIN not changed. Try again!")
                    return
                query="UPDATE accounts SET atm_pin=%s WHERE account_number=%s"
                values=(new_pin,account_number)
                self.cursor.execute(query,values)
                self.conn.commit()
                print("ATM PIN updated successfully...")
            else:
                print("Incorrect old pin.")
        else:
            print("Account not found. Please enter correct details")

    def account_statement(self):
        account_number=input("Enter account number: ")
        atm_pin=input("Enter ATM PIN: ")
        query="SELECT atm_pin from accounts where account_number=%s"
        self.cursor.execute(query,(account_number,))
        result=self.cursor.fetchone()
        if self.check_account(account_number) and atm_pin==result[0]:
            query="SELECT * FROM transactions where from_account=%s OR to_account=%s"
            values=(account_number,account_number)
            self.cursor.execute(query,values)
            result=self.cursor.fetchall()
            if not result:
                print("No transactions found for this account.")
                return
            print("\n--- Account Statement ---")
            for txn in result:
                print("Transaction Id: ",txn[0]," From: ",txn[1]," To: ",txn[2],end=' ')
                print("Amount: ",txn[3],"Date & Time: ",txn[4])
            filename="account_statement_"+account_number+".csv"
            with open(filename, mode="w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Transaction Id", "From Account", "To Account", "Amount", "Date & Time"])
                writer.writerows(result)
            print("Account Statement saved to",filename)
        else:
            print("Account not found. Please enter correct details")

    def apply_loan(self):
        account_number = input("Enter account number: ")
        if not self.check_account(account_number):
            print("Account not found. Please enter correct details.")
            return
        try:
            loan_amount = float(input("Enter loan amount: "))
            emi = float(input("Enter monthly EMI amount: "))
            tenure = int(input("Enter tenure in years: "))
            loan_type = input("Enter loan type (home/personal): ").strip().lower()
            if loan_type not in ["home", "personal"]:
                print("Invalid loan type. Must be 'home' or 'personal'.")
                return
        except ValueError:
            print("Invalid input. Please enter numeric values for amount, EMI, and tenure.")
            return
        total_months = tenure * 12
        total_payable = emi * total_months
        start_date = date.today()
        end_date = start_date.replace(year=start_date.year + tenure)
        query = '''
            INSERT INTO loans (account_number, amount, emi, tenure, type, total_payable, start_date, end_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        '''
        values = (account_number, loan_amount, emi, tenure, loan_type, total_payable, start_date, end_date)
        self.cursor.execute(query, values)
        query = "UPDATE accounts SET balance = balance + %s WHERE account_number = %s"
        self.cursor.execute(query, (loan_amount, account_number))
        query = "INSERT INTO transactions (from_account, to_account, amount) VALUES (%s, %s, %s)"
        self.cursor.execute(query, ("bank", account_number, loan_amount))
        self.conn.commit()
        print("Loan sanctioned...")

    def get_report(self):
        query="SELECT name,account_number,balance FROM accounts ORDER BY balance DESC"
        self.cursor.execute(query)
        result=self.cursor.fetchall()
        print("--- All Account Details Sorted By Balance ---")
        for acc in result:
            print("Name: ",acc[0]," Account Number: ",acc[1]," Balance: ",acc[2])

    def close(self):
        print("Disconnected from MySQL Database.")
        self.cursor.close()
        self.conn.close()

def main():
    bank=Bank()
    while True:
        print("1. Create Account")
        print("2. Access Account")
        print("3. Transfer Funds")
        print("4. Account Statement")
        print("5. Apply Interest To All Accounts")
        print("6. Create Fixed Deposit")
        print("7. Apply For Loan")
        print("8. Change ATM PIN")
        print("9. Reporting & Analytics")
        print("10. Exit")
        choice=int(input("Enter your choice: "))
        if choice==1:
            bank.create_account()
        elif choice==2:
            bank.access_account()
        elif choice==3:
            bank.transfer_funds()
        elif choice==4:
            bank.account_statement()
        elif choice==5:
            bank.apply_interest()
        elif choice==6:
            bank.create_fixed_deposit()
        elif choice==7:
            bank.apply_loan()
        elif choice==8:
            bank.change_atm_pin()
        elif choice==9:
            bank.get_report()
        else:
            bank.close()
            print("Successfully exited...")
            break

if __name__ == "__main__":
    main()