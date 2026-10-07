# Latest Amazon Linux 2023 AMI for x86_64, looked up at plan time instead of
# hard-coding an AMI ID (IDs differ per region and change with every release).
data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-kernel-6.1-x86_64"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "web" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web.id]

  # The page shows the bucket name, which creates an implicit dependency on the
  # S3 bucket through the template variables.
  user_data = templatefile("${path.module}/user_data.sh.tftpl", {
    project     = var.project
    bucket_name = aws_s3_bucket.assets.bucket
  })
  user_data_replace_on_change = true

  # IMDSv2 only: metadata requests need a session token.
  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  root_block_device {
    volume_type = "gp3"
    volume_size = 8
    encrypted   = true
  }

  # Explicit dependency. Nothing in this resource refers to the route table, so
  # Terraform would happily start the instance before the 0.0.0.0/0 route exists.
  # user_data runs "dnf install nginx" at first boot and needs that route, so
  # wait for the subnet to be associated with the public route table.
  depends_on = [aws_route_table_association.public]

  tags = {
    Name = "${var.project}-web"
  }
}
