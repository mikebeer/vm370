program Strings;
var
  s, t, u: string;
  c: char;
  i, n: integer;
begin
  s := 'Hello';
  t := 'World';
  u := s + ', ' + t + '!';
  writeln(u);
  writeln('length = ', length(u));
  writeln('copy   = ', copy(u, 8, 5));
  writeln('pos    = ', pos('World', u));
  writeln('upper  = ', upcase(u));
  c := u[1];
  writeln('first  = ', c, ' code ', ord(c));
  writeln('chr    = ', chr(65), chr(ord('a') + 1));
  for i := length(s) downto 1 do write(s[i]);
  writeln;
  if s < t then writeln('Hello < World');
  if s + t = 'HelloWorld' then writeln('concat equal');
  delete(u, 6, 2);
  writeln(u);
  insert('Pascal ', u, 7);
  writeln(u);
  str(12345, t);
  writeln('[', t, ']');
  val('987', n, i);
  writeln(n + 1, ' ', i);
  val('9x7', n, i);
  writeln('code ', i);
  s := '';
  for i := 1 to 5 do s := s + chr(64 + i);
  writeln(s);
end.
