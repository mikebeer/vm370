;;; reading standard input
(let ((line (read-line)))
  (format t "first line: ~A~%" line))
(let ((total 0) (count 0))
  (loop for line = (read-line nil nil)
        while line
        do (incf total (parse-integer line))
           (incf count))
  (format t "~D numbers, sum ~D~%" count total))
