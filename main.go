package main

import (
	cadastrodeoperador "estacionamento/cadastroDeOperador"
	cadastromensalista "estacionamento/cadastroMensalista"
	"estacionamento/dataBase"
	"estacionamento/entradaDeVeiculos"
	saidadeveiculos "estacionamento/saidaDeVeiculos"
	"fmt"
	"log"
	"time"
)

func init() {
	// Inicializar validação de senha do operador
	var id, cod, nome, senha, tipo, codProcurado, senhaProcurada string
	var autorizado = false

	fmt.Printf("Digite o usuário:")
	fmt.Scanln(&cod)

	fmt.Printf("Digite a senha:")
	fmt.Scanln(&senha)

	db, erro := dataBase.ConexaoBanco()
	if erro != nil {
		log.Fatal("Erro co conectar ao banco de dados")
	}
	defer db.Close()

	linhas, err := db.Query("SELECT * FROM estacionamento.cadastroOperador")

	if err != nil {
		log.Fatal("Erro ao criar o statement cobrança", err)
	}
	defer linhas.Close()

	for linhas.Next() {
		if err := linhas.Scan(&id, &codProcurado, &nome, &senhaProcurada, &tipo); err != nil {
			log.Fatal("Erro ao buscar os valores no banco", err)
		}
		if cod == codProcurado {
			if senha == senhaProcurada {
				autorizado = true
				break
			}
		}
	}
	if !autorizado {
		defer log.Fatal()
		fmt.Println("Usuário não cadastrado ou senha inválida")
		fmt.Println("Saindo do sistema...")
		time.Sleep(time.Second * 5)
	}
}

func main() {

	fmt.Println("\n\tPROJETO ESTACIONAMENTO")

	for {
		var rot int
		linhas()
		fmt.Println("\n| 1 - ENTRADA DE VEICULO\t|")
		fmt.Println("| 2 - SAIDA DE VEICULO\t\t|")
		fmt.Println("| 3 - CADASTRA OPERADOR\t\t|")
		fmt.Println("| 4 - CADASTRO DE MENSALISTA\t|")
		linhas()
		fmt.Printf("\n\nDigite uma opção:")
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

func linhas() {
	for i := 1; i < 34; i++ {
		//if i == 1 {
		//	fmt.Printf("|")
		//}
		fmt.Printf("=")
		if i == 34 {
			fmt.Println("|")
		}
	}
}
