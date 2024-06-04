package cadastromensalista

import (
	"bufio"
	"estacionamento/dataBase"
	"fmt"
	"log"
	"os"
	"strings"
)

func Cadastro() {
	var cpfCnpj, nome, placa string

	fmt.Println("Cadastro de Mensalista")

	fmt.Printf("CPD/CNPJ Somente Números:")
	fmt.Scanln(&cpfCnpj)

	fmt.Printf("Nome completo:")
	nome = strings.ToUpper(nome)
	// Usando bufio.NewReader para ler toda a linha
	reader := bufio.NewReader(os.Stdin)
	nome, _ = reader.ReadString('\n')
	// Removendo o caractere de nova linha do final
	nome = strings.TrimSpace(nome)

	fmt.Printf("Placa do veiculo:")
	fmt.Scanln(&placa)

	db, err := dataBase.ConexaoBanco()
	if err != nil {
		log.Fatal("Erro ao fazer a primeira tentativa de conectar ao banco de dados")
	}
	defer db.Close()

	statement, err := db.Prepare("insert into mensalista (cpfCnpj, nome, placa) values (?, ?, ?)")

	if err != nil {
		log.Fatal("Erro ao conectar no banco de dados", err)
	}

	resultado, err := statement.Exec(cpfCnpj, nome, placa)

	if err != nil {
		log.Fatal("Erro ao gravar os dados no banco de dados", err, resultado)
	} else {
		fmt.Println("Dados Gravados com Sucesso", cpfCnpj, "-", nome, "-", placa)
		fmt.Scanln()
	}

}
