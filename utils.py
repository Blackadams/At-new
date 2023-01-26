
from __future__ import print_function
import africastalking

class MobileWallet:
    def __init__(self):
        # Set your app credentials
        self.username = "shoppay"
        self.api_key = "f8a1ee5aad8455e96b2296669e524288bdc78959511aafd0db71b0588b21bb6e"

        # Initialize the SDK
        africastalking.initialize(self.username, self.api_key)

        # Get the airtime service
        self.airtime = africastalking.Airtime

    def topup(self, phone_number, amount, currency_code):
        try:
            # Send airtime to the number provided
            responses = self.airtime.send(phone_number=phone_number, amount=amount, currency_code=currency_code)
            print(responses)
        except Exception as e:
            print("Encountered an error while topping up: %s" %str(e))

    def pay(self, phone_number, amount, currency_code):
        try:
            # Send airtime from the user's number
            responses = self.airtime.transfer(phone_number=phone_number, amount=amount, currency_code=currency_code)
            print(responses)
        except Exception as e:
            print("Encountered an error while making payment: %s" %str(e))

    def check_balance(self):
        try:
            # check account balance
            balance = self.airtime.check_balance()
            print(balance)
        except Exception as e:
            print("Encountered an error while checking balance: %s" %str(e))

# if __name__ == '__main__':
#     Create an instance of the class
#     wallet = MobileWallet()
#     Top up user's account
#     wallet.topup("+254123456789", "10", "KES")
#     Make a payment
#     wallet.pay("+254123456789", "5", "KES")
#     check account balance
#     wallet.check_balance()


