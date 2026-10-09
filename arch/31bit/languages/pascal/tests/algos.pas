program Algos;
const
  N = 8;
  Size = 10;
type
  IntArray = array[1..Size] of integer;
  Matrix = array[1..3, 1..3] of integer;
var
  a: IntArray;
  m1, m2, m3: Matrix;
  i, j, k: integer;
  col: array[1..N] of integer;
  solutions: integer;
  moves: integer;

procedure BubbleSort(var arr: IntArray);
var i, j, t: integer;
begin
  for i := 1 to Size - 1 do
    for j := 1 to Size - i do
      if arr[j] > arr[j + 1] then begin
        t := arr[j]; arr[j] := arr[j + 1]; arr[j + 1] := t;
      end;
end;

procedure QuickSort(var arr: IntArray; lo, hi: integer);
var i, j, p, t: integer;
begin
  if lo >= hi then exit;
  p := arr[(lo + hi) div 2];
  i := lo; j := hi;
  while i <= j do begin
    while arr[i] < p do i := i + 1;
    while arr[j] > p do j := j - 1;
    if i <= j then begin
      t := arr[i]; arr[i] := arr[j]; arr[j] := t;
      i := i + 1; j := j - 1;
    end;
  end;
  QuickSort(arr, lo, j);
  QuickSort(arr, i, hi);
end;

function Sum(arr: IntArray): integer;   { passed by value: copied }
var i, s: integer;
begin
  s := 0;
  for i := 1 to Size do s := s + arr[i];
  arr[1] := 999;
  Sum := s;
end;

function Safe(r, c: integer): boolean;
var i: integer;
begin
  Safe := true;
  for i := 1 to r - 1 do
    if (col[i] = c) or (abs(col[i] - c) = r - i) then Safe := false;
end;

procedure Place(r: integer);
var c: integer;
begin
  if r > N then begin
    solutions := solutions + 1;
    exit;
  end;
  for c := 1 to N do
    if Safe(r, c) then begin
      col[r] := c;
      Place(r + 1);
    end;
end;

procedure Hanoi(n: integer; from, dest, via: integer);
begin
  if n = 0 then exit;
  Hanoi(n - 1, from, via, dest);
  moves := moves + 1;
  Hanoi(n - 1, via, dest, from);
end;

function IsEven(n: integer): boolean; forward;
function IsOdd(n: integer): boolean;
begin
  if n = 0 then IsOdd := false else IsOdd := IsEven(n - 1);
end;
function IsEven;
begin
  if n = 0 then IsEven := true else IsEven := IsOdd(n - 1);
end;

begin
  for i := 1 to Size do a[i] := (i * 7) mod 11;
  for i := 1 to Size do write(a[i], ' ');
  writeln;
  BubbleSort(a);
  for i := 1 to Size do write(a[i], ' ');
  writeln;
  for i := 1 to Size do a[i] := (i * 5) mod 13;
  QuickSort(a, 1, Size);
  for i := 1 to Size do write(a[i], ' ');
  writeln;
  writeln('sum = ', Sum(a), ' a[1] = ', a[1]);
  for i := 1 to 3 do
    for j := 1 to 3 do begin
      m1[i, j] := i + j;
      m2[i, j] := i * j;
    end;
  for i := 1 to 3 do
    for j := 1 to 3 do begin
      m3[i, j] := 0;
      for k := 1 to 3 do m3[i, j] := m3[i, j] + m1[i, k] * m2[k, j];
    end;
  for i := 1 to 3 do begin
    for j := 1 to 3 do write(m3[i, j]:4);
    writeln;
  end;
  solutions := 0;
  Place(1);
  writeln(N, ' queens: ', solutions, ' solutions');
  moves := 0;
  Hanoi(10, 1, 3, 2);
  writeln('hanoi 10: ', moves, ' moves');
  writeln(IsEven(10), ' ', IsOdd(7), ' ', IsEven(7));
end.
