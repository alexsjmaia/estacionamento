package dataBase

import (
	"database/sql"

	_ "github.com/go-sql-driver/mysql" // Driver
)

// ConexaoBanco abre a conexão com o banco de dados e retorna
func ConexaoBanco() (*sql.DB, error) {
	stringConexao := "root:260803@/estacionamento?charset=utf8&parseTime=True&loc=Local"
	db, err := sql.Open("mysql", stringConexao)
	if err != nil {
		return nil, err
	}
	if err = db.Ping(); err != nil {
		db.Close()
		return nil, err
	}
	return db, nil
}
