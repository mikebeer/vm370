;;; small complete programs
;; sieve of Eratosthenes
(defun sieve (n)
  (let ((flags (make-array (1+ n) :initial-element t)) (primes nil))
    (loop for i from 2 to n
          do (when (aref flags i)
               (push i primes)
               (loop for j from (* i i) to n by i do (setf (aref flags j) nil))))
    (nreverse primes)))
(print (sieve 60))

;; fizzbuzz
(dotimes (i 15)
  (let ((n (1+ i)))
    (format t "~A " (cond ((zerop (mod n 15)) "FizzBuzz") ((zerop (mod n 3)) "Fizz") ((zerop (mod n 5)) "Buzz") (t n)))))
(terpri)

;; towers of hanoi
(defvar *moves* 0)
(defun hanoi (n from to via)
  (when (> n 0)
    (hanoi (1- n) from via to)
    (incf *moves*)
    (hanoi (1- n) via to from)))
(hanoi 10 'a 'c 'b)
(print *moves*)

;; quicksort and merge sort
(defun quicksort (l)
  (if (null l) nil
      (let ((p (car l)) (rest (cdr l)))
        (append (quicksort (remove-if-not (lambda (x) (< x p)) rest))
                (list p)
                (quicksort (remove-if (lambda (x) (< x p)) rest))))))
(print (quicksort '(3 1 4 1 5 9 2 6 5 3 5)))
(defun merge-lists (a b)
  (cond ((null a) b) ((null b) a)
        ((< (car a) (car b)) (cons (car a) (merge-lists (cdr a) b)))
        (t (cons (car b) (merge-lists a (cdr b))))))
(defun msort (l)
  (if (or (null l) (null (cdr l))) l
      (let* ((half (floor (length l) 2)))
        (merge-lists (msort (subseq l 0 half)) (msort (subseq l half))))))
(print (msort '(8 3 5 1 9 2 7)))

;; n queens
(defun queens (n)
  (let ((count 0) (cols (make-array n :initial-element 0)))
    (labels ((ok (row col)
               (dotimes (r row t)
                 (let ((c (aref cols r)))
                   (when (or (= c col) (= (abs (- c col)) (- row r)))
                     (return nil)))))
             (place (row)
               (if (= row n)
                   (incf count)
                   (dotimes (col n)
                     (when (ok row col)
                       (setf (aref cols row) col)
                       (place (1+ row)))))))
      (place 0))
    count))
(print (list (queens 4) (queens 5) (queens 6)))

;; symbolic differentiation
(defun d (e x)
  (cond ((numberp e) 0)
        ((symbolp e) (if (eq e x) 1 0))
        ((eq (car e) '+) (list '+ (d (cadr e) x) (d (caddr e) x)))
        ((eq (car e) '*) (list '+ (list '* (cadr e) (d (caddr e) x))
                                  (list '* (d (cadr e) x) (caddr e))))
        (t (error "unknown operator ~S" (car e)))))
(print (d '(+ (* 3 x) (* x x)) 'x))

;; association list word count
(defun count-words (words)
  (let ((table nil))
    (dolist (w words)
      (let ((entry (assoc w table)))
        (if entry (incf (cdr entry)) (push (cons w 1) table))))
    (sort table #'> :key #'cdr)))
(print (count-words '(a b a c b a)))

;; string processing
(defun palindromep (s)
  (let ((clean (remove-if-not #'alpha-char-p (string-downcase s))))
    (string= clean (reverse clean))))
(print (list (palindromep "A man, a plan, a canal: Panama") (palindromep "hello")))
(defun split-string (s ch)
  (let ((parts nil) (start 0))
    (dotimes (i (length s))
      (when (char= (char s i) ch)
        (push (subseq s start i) parts)
        (setq start (1+ i))))
    (push (subseq s start) parts)
    (nreverse parts)))
(print (split-string "a,b,,c" #\,))

;; collatz, gcd, primes
(defun collatz-len (n) (let ((c 1)) (loop until (= n 1) do (setq n (if (evenp n) (/ n 2) (+ (* 3 n) 1))) (incf c)) c))
(print (collatz-len 27))
(print (loop for n from 1 to 30 maximize (collatz-len n)))

;; bank account with closures
(defun make-account (balance)
  (lambda (op &optional amount)
    (case op
      (deposit (incf balance amount))
      (withdraw (if (> amount balance) (error "insufficient funds") (decf balance amount)))
      (balance balance))))
(let ((acc (make-account 100)))
  (funcall acc 'deposit 50)
  (funcall acc 'withdraw 30)
  (print (funcall acc 'balance))
  (print (handler-case (funcall acc 'withdraw 500) (error (e) (format nil "error: ~A" e)))))

;; binary trees
(defun tree-insert (tree x)
  (cond ((null tree) (list x nil nil))
        ((< x (car tree)) (list (car tree) (tree-insert (cadr tree) x) (caddr tree)))
        (t (list (car tree) (cadr tree) (tree-insert (caddr tree) x)))))
(defun tree-inorder (tree)
  (if (null tree) nil
      (append (tree-inorder (cadr tree)) (list (car tree)) (tree-inorder (caddr tree)))))
(print (tree-inorder (reduce #'tree-insert '(5 3 8 1 4 7 9 2 6) :initial-value nil)))

;; a tiny interpreter
(defun ev (e env)
  (cond ((numberp e) e)
        ((symbolp e) (cdr (assoc e env)))
        ((eq (car e) 'let1) (ev (cadddr e) (acons (cadr e) (ev (caddr e) env) env)))
        ((eq (car e) 'if0) (if (zerop (ev (cadr e) env)) (ev (caddr e) env) (ev (cadddr e) env)))
        (t (apply (case (car e) (add #'+) (mul #'*) (sub #'-))
                  (mapcar (lambda (a) (ev a env)) (cdr e))))))
(print (ev '(let1 x 5 (add x (mul x 2))) nil))
(print (ev '(if0 (sub 3 3) 100 200) nil))
