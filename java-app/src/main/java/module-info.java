module com.example.passwordmanager {
    requires javafx.controls;
    requires javafx.fxml;


    opens com.example.passwordmanager to javafx.fxml;
    exports com.example.passwordmanager;
    exports com.example.passwordmanager.Controller;
    opens com.example.passwordmanager.Controller to javafx.fxml;
}