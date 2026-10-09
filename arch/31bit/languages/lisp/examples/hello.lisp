(defun greet (name)
  (format t "Hello, ~A!~%" name))

(greet "world")
(print (loop for i from 1 to 5 collect (* i i)))
