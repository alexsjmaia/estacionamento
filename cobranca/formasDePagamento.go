package cobranca

import (
	"estacionamento/dataBase"
	"fmt"
	"log"
)

var (
	num, descricao string
)

func formaDePagamento(valorCobrado float64) {

	db, erro := dataBase.ConexaoBanco()
	if erro != nil {
		log.Fatal("Erro co conectar ao banco de dados")
	}
	defer db.Close()

	linhas, err := db.Query("SELECT num, descricao FROM estacionamento.tiposDePagamentos")
	if err != nil {
		log.Fatal("Erro ao criar o statement formaDePagamento", err)
	}
	defer linhas.Close()

	if linhas.Next() {
		if err := linhas.Scan(&num, &descricao); err != nil {
			log.Fatal("Erro ao buscar as formas de pagamento no banco", err)
		}
	}
	fmt.Printf("O tipo da variável é: %T\n", linhas)

	fmt.Println("O Valor Cobrado Pela estádia é ", valorCobrado)
	log.Fatal("Cheguei longe")
}
