from app.mailing.mailPubSub import MailPubSub

def main():
    pub_sub=MailPubSub()
    pub_sub.spinup_subscription()

if __name__ == '__main__':
    main()