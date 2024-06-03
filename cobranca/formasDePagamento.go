package cobranca

import "fmt"

func FormasDePagamento(valorCobrado float64) string {
	var opcao uint
	var descricao string

	fmt.Println("1 - PIX\n2 - Dinheiro\n3 - Cartão\t")
	fmt.Printf("Digite uma opção:")
	fmt.Scanln(&opcao)

	switch opcao {
	case 1:
		descricao = "PIX"
	case 2:
		CalculaPagamento(valorCobrado)
		descricao = "Dinheiro"
	case 3:
		descricao = "Cartão"
	default:
		FormasDePagamento(valorCobrado)
	}
	return descricao
}
