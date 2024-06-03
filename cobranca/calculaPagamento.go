package cobranca

import "fmt"

func CalculaPagamento(valorCobrado float64) {
	var valorRecebido float64

	fmt.Printf("Digite o Recebido em Dinheiro :")
	fmt.Scanln(&valorRecebido)

	if valorRecebido < valorCobrado {
		valorRecebido = 0
		fmt.Println("Valor Recebido é menor que o valor Cobrado")
		CalculaPagamento(valorCobrado)
	} else {
		fmt.Printf("\nValor Recebido \tR$ %.2f\n", valorRecebido)
		fmt.Printf("Valor Cobrado \tR$ %.2f\n", valorCobrado)
		fmt.Printf("Valor do Troco \tR$ %.2f\n\n", valorRecebido-valorCobrado)
	}
}
