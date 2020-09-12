// verify-helper: PROBLEM https://onlinejudge.u-aizu.ac.jp/courses/library/3/DSL/all/DSL_1_A
pub mod union_find;
use union_find::union_find::UnionFind;

use std::io::*;
use std::str::FromStr;

fn read<T: FromStr>() -> T {
    let stdin = stdin();
    let stdin = stdin.lock();
    let token: String = stdin
        .bytes()
        .map(|c| c.expect("failed to read char") as char) 
        .skip_while(|c| c.is_whitespace())
        .take_while(|c| !c.is_whitespace())
        .collect();
    token.parse().ok().expect("failed to parse token")
}

fn main(){
    let n:usize=read();
    let q:usize=read();
    let mut uf=UnionFind::new(n);
    for i in 0..q{
        let c:usize=read();
        let s:usize=read();
        let t:usize=read();
        if c==0{
            uf.merge(s,t);
        }else{
            println!("{}",if uf.same(s,t){1}else{0});
        }
    }
}

