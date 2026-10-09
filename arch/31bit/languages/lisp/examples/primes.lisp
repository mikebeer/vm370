;;; Primes by trial division, and by the sieve of Eratosthenes.
(defun primep (n)
  (and (> n 1)
       (loop for d from 2 to (isqrt n)
             never (zerop (mod n d)))))

(defun primes-below (n)
  (loop for i from 2 below n
        when (primep i) collect i))

(defun sieve (n)
  (let ((flags (make-array (1+ n) :initial-element t))
        (primes nil))
    (loop for i from 2 to n
          do (when (aref flags i)
               (push i primes)
               (loop for j from (* i i) to n by i
                     do (setf (aref flags j) nil))))
    (nreverse primes)))

(format t "Primes below 50: ~A~%" (primes-below 50))
(format t "Sieve to 50:     ~A~%" (sieve 50))
(format t "There are ~D primes below 1000.~%" (length (sieve 1000)))
