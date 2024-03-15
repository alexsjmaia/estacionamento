package main

import (
	"estacionamento/entradaDeVeiculos"
	saidadeveiculos "estacionamento/saidaDeVeiculos"
	"fmt"
)

func main() {
	fmt.Println("PROJETO ESTACIONAMENTO")
	for {
		var rot int
		fmt.Println("1 - ENTRADA DE VEICULO")
		fmt.Println("2 - SAIDA DE VEICULO")
		fmt.Printf("Digite uma opção:")
		fmt.Scanln(&rot)

		if rot == 1 {
			entradaDeVeiculos.Entrada()
		} else if rot == 2 {
			saidadeveiculos.SaidaDeveiculos()
		}
	}
}
