program Sieve;
const N = 100;
var
  flag: array[2..N] of boolean;
  i, j, count: integer;
begin
  for i := 2 to N do flag[i] := true;
  for i := 2 to N do
    if flag[i] then begin
      j := i * i;
      while j <= N do begin
        flag[j] := false;
        j := j + i;
      end;
    end;
  count := 0;
  for i := 2 to N do
    if flag[i] then begin
      write(i:4);
      count := count + 1;
      if count mod 10 = 0 then writeln;
    end;
  writeln;
  writeln(count, ' primes up to ', N);
end.
