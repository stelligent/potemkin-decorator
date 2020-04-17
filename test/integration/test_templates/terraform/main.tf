locals{
    random = formatdate("YYYYMMDDhhmmss", timestamp())
}

resource "aws_config_config_rule" "rule" {
    name = "eip-attached-${local.random}"

    source {
        owner             = "AWS"
        source_identifier = "EIP_ATTACHED"
    }

    scope {
        compliance_resource_types = ["AWS::EC2::EIP"]
    }
    lifecycle {ignore_changes = [name] }
}

resource "aws_eip" "eip1" {
    vpc  = true
    tags = {
        Name = "potemkin-test-eip1-${local.random}"
    }
    lifecycle {ignore_changes = [tags] }
}

resource "aws_eip" "eip2" {
    vpc  = true
    tags = {
        Name = "potemkin-test-eip1-${local.random}"
    }
    lifecycle {ignore_changes = [tags]}
}

output "ConfigRuleName" {
    value = aws_config_config_rule.rule.name
}
output "EIPOutput" {
    value = aws_eip.eip1.id
}
output "EIP2Output" {
    value = aws_eip.eip2.id
}
