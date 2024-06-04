package main

import (
	cadastrodeoperador "estacionamento/cadastroDeOperador"
	cadastromensalista "estacionamento/cadastroMensalista"
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
		fmt.Println("3 - CADASTRA OPERADOR")
		fmt.Println("4 - CADASTRO DE MENSALISTA")
		fmt.Printf("Digite uma opção:")
		fmt.Scanln(&rot)

		if rot == 1 {
			entradaDeVeiculos.Entrada()
		} else if rot == 2 {
			saidadeveiculos.SaidaDeveiculos()
		} else if rot == 3 {
			cadastrodeoperador.Cadastro()
		} else if rot == 4 {
			cadastromensalista.Cadastro()
		}
	}
}
