;;; A bank account made of a closure, with error handling.
(defun make-account (balance)
  (lambda (op &optional amount)
    (case op
      (deposit  (incf balance amount))
      (withdraw (if (> amount balance)
                    (error "insufficient funds: balance ~D, wanted ~D" balance amount)
                    (decf balance amount)))
      (balance  balance)
      (t (error "unknown operation ~S" op)))))

(defvar *acc* (make-account 100))

(funcall *acc* 'deposit 50)
(format t "Balance: ~D~%" (funcall *acc* 'balance))
(funcall *acc* 'withdraw 30)
(format t "Balance: ~D~%" (funcall *acc* 'balance))

(dolist (amount '(20 500))
  (handler-case
      (progn (funcall *acc* 'withdraw amount)
             (format t "Withdrew ~D~%" amount))
    (error (e)
      (format t "Refused: ~A~%" e))))
(format t "Final balance: ~D~%" (funcall *acc* 'balance))
